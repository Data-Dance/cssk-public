import json

from odoo import _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError

_lt = LazyTranslate(__name__)


class CSSKControlStatement(models.Model):
    """The control-statement aggregate (KV DPH / KH DPH).

    Lifecycle: draft → preview (lines computed) → exported (XML attached) →
    submitted. Country modules extend this with per-section O2M fields and
    override ``_collect_sections_by_code``.
    """

    _name = "cssk.control.statement"
    _description = "VAT Control Statement (KV DPH / KH DPH)"
    # Two mixins, two concerns, both wanted: the statutory one retains the
    # filed copy, the submittable one tracks whether it arrived and holds what
    # came back. Neither substitutes for the other — a daňová kontrola asks for
    # the doručenka, which only the second can produce.
    _inherit = ["mail.thread", "mail.activity.mixin",
                "cssk.statutory.submission.mixin",
                "cssk.submittable.mixin"]
    _order = "date_from desc, id desc"

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    country_id = fields.Many2one(
        related="company_id.account_fiscal_country_id", store=True
    )

    version_id = fields.Many2one(
        "cssk.control.statement.version",
        required=True,
        domain="[('country_id', '=', country_id),"
        " ('valid_from', '<=', date_to),"
        " '|', ('valid_to', '=', False), ('valid_to', '>=', date_from)]",
        # The dropdown must offer an ARCHIVED vintage too. The domain
        # above already scopes by period, so a 2026 filing never sees
        # the 2014 vzor anyway — archiving is a way of tidying the
        # configuration list, and it must not quietly make an old
        # period unenterable or a historical filing un-repointable.
        context={'active_test': False},
    )

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    period_type = fields.Selection(
        [("month", "Monthly"), ("quarter", "Quarterly")], required=True
    )
    statement_type_id = fields.Many2one(
        "cssk.control.statement.type",
        # Country, not version: riadny / opravný / dodatočný is a property of
        # the form family and does not change when a vzor does. See the type
        # model's docstring for the evidence.
        domain="[('country_id', '=', country_id)]",
        required=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("exported", "Exported"),
            ("submitted", "Submitted"),
            ("cancelled", "Cancelled"),
            # Terminal, and off the workflow rather than at the end of it. A
            # historical filing was completed and submitted years ago by
            # whoever ran the previous system; it is a RECORD of a filing, not
            # a filing in progress, so no transition leads into or out of it.
            # Set automatically whenever ``legacy`` is set — see
            # ``cssk.statutory.submission.mixin``, which owns that rule so the
            # importer cannot set one without the other.
            ("legacy", "Historical filing"),
        ],
        default="draft",
        tracking=True,
    )

    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)
    original_return_id = fields.Many2one(
        "cssk.control.statement", string="Amends", copy=False, readonly=True,
        index=True,
        help="The originally-filed statement this amended / corrective statement amends.")
    amendment_ids = fields.One2many(
        "cssk.control.statement", "original_return_id", string="Amendments")
    kv_full_state_json = fields.Text(
        readonly=True, copy=False,
        help="Snapshot of the FULL transaction list this amended KV represents "
             "(before it is reduced to a delta). It is the baseline the NEXT "
             "amendment diffs against, so chained amended statements stay correct.")

    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for st in self:
            st.name = "KV/KH %s — %s" % (
                st.date_from or "",
                st.date_to or "",
            )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only draft statements can be recomputed."))
        # Preserve manual overrides across the destructive repopulate —
        # mirrors the VAT return (snapshot → wipe → repopulate → re-apply;
        # unmatched overrides go to the chatter, never silently lost).
        overrides = self._kv_collect_overrides()
        self._clear_existing_sections()
        for code in self.version_id.section_code_ids.sorted("sequence"):
            self.env[code.section_model]._populate_for_statement(self, code)
        self._kv_reapply_overrides(overrides)
        # A dodatočný KV reports only the delta vs the original (with kód opravy);
        # a riadny / opravný keeps the full freshly-computed list. Snapshot the
        # FULL list first (it is the baseline the *next* amendment diffs against),
        # then reduce the visible sections to the delta.
        if self.original_return_id and self._is_dodatocny():
            self.kv_full_state_json = json.dumps(self._kv_collect_snapshots())
            self._apply_dodatocny_delta()
        self.state = "preview"

    def _clear_existing_sections(self):
        for code in self.version_id.section_code_ids:
            self.env[code.section_model].search(
                [("statement_id", "=", self.id)]
            ).unlink()

    # ------------------------------------------------------------------
    # Manual overrides across recompute (see the row mixins)
    # ------------------------------------------------------------------
    def _kv_collect_overrides(self):
        """Snapshot the user-overridden rows before the sections are wiped:
        ``{section_code: {override_key: {field: value}}}``."""
        self.ensure_one()
        out = {}
        for code, rows in self._collect_sections_by_code().items():
            for row in rows:
                if "is_overridden" not in row._fields or not row.is_overridden:
                    continue
                out.setdefault(code, {})[row._kv_override_key()] = (
                    row._kv_override_values())
        return out

    def _kv_reapply_overrides(self, overrides):
        """Re-apply the snapshotted overrides onto the freshly repopulated
        section rows (matched by ``_kv_override_key``); post a chatter
        warning listing overrides whose row no longer exists."""
        self.ensure_one()
        if not overrides:
            return {}
        sections = self._collect_sections_by_code()
        lost = {}
        for code, mapping in overrides.items():
            remaining = dict(mapping)
            for row in sections.get(code, []):
                if not remaining:
                    break
                key = row._kv_override_key()
                if key in remaining:
                    row.write(dict(remaining.pop(key), is_overridden=True))
            if remaining:
                lost[code] = remaining
        if lost:
            self.message_post(body=_(
                "Recompute dropped %(count)s manual override(s) whose row no "
                "longer exists in the recomputed statement:\n%(rows)s",
                count=sum(len(m) for m in lost.values()),
                rows="\n".join(
                    "  • %s: %s" % (code, " / ".join(str(p) for p in key))
                    for code, mapping in sorted(lost.items())
                    for key in sorted(mapping))))
        return lost

    def _is_dodatocny(self):
        self.ensure_one()
        return (self.statement_type_id.fa_xml_value or "").upper() == "D"

    def _kv_collect_snapshots(self):
        """{code: [row-snapshot dict]} of the current (full) sections."""
        self.ensure_one()
        return {code: [r._kv_snapshot() for r in rows]
                for code, rows in self._collect_sections_by_code().items()}

    def _kv_baseline(self):
        """The last-known **full** transaction list to diff against.

        For a riadny / opravný predecessor its stored sections ARE the full list.
        For a prior dodatočný predecessor the stored sections are only ITS delta,
        so the cumulative full state lives in ``kv_full_state_json`` — this is
        what keeps chained dodatočné výkazy correct."""
        self.ensure_one()
        orig = self.original_return_id
        if orig._is_dodatocny():
            return json.loads(orig.kv_full_state_json or "{}")
        return orig._kv_collect_snapshots()

    def _kv_create_storno(self, model_name, snap):
        """Create a storno row (KOpr=1) from a baseline snapshot on this stmt."""
        vals = dict(snap["vals"], statement_id=self.id, kod_opravy="1")
        self.env[model_name].create(vals)

    def _apply_dodatocny_delta(self):
        """Turn the freshly-computed full sections into the **dodatočný KV
        delta** vs the last-known full state (``_kv_baseline``): only changed
        rows survive, each tagged kód opravy — 2 (nové / správne) for added or
        corrected rows, 1 (storno) for the original values of corrected or
        removed rows. Unchanged rows are dropped (a dodatočný KV repeats only
        what changed, § 78a ods. 4 zákona o DPH; poučenie KV DPH — kód opravy
        1/2)."""
        self.ensure_one()
        baseline = self._kv_baseline()
        new_sections = self._collect_sections_by_code()
        for code, new_rows in new_sections.items():
            base_list = baseline.get(code, [])
            index = {}
            for snap in base_list:
                index.setdefault(tuple(snap["id"]), []).append(snap)
            used = set()
            drop = new_rows.browse()
            stornos = []
            for nr in new_rows:
                free = [s for s in index.get(tuple(nr._kv_identity()), [])
                        if id(s) not in used]
                if not free:
                    nr.kod_opravy = "2"                 # nový riadok
                    continue
                snap = free[0]
                used.add(id(snap))
                if list(nr._kv_values()) == list(snap["v"]):
                    drop |= nr                          # nezmenený -> mimo dodatočného
                else:
                    nr.kod_opravy = "2"                 # zmenené -> nové údaje
                    stornos.append(snap)                # + storno pôvodných
            for snap in base_list:
                if id(snap) not in used:
                    stornos.append(snap)                # zrušený -> storno
            drop.unlink()
            for snap in stornos:
                self._kv_create_storno(new_rows._name, snap)

    # ------------------------------------------------------------------
    # Export — the pipeline lives in cssk.statutory.submission.mixin;
    # only the form-specific hooks are parameterized here. NB: kontrolné
    # pravidlá now run BEFORE rendering (the standardized order).
    # ------------------------------------------------------------------
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("control statement")
    _cssk_xml_name_fallback = "control_statement"

    def _cssk_check_kontroly(self):
        self.ensure_one()
        self._cssk_enforce_kontroly()
        return True

    # ------------------------------------------------------------------
    # kontrolné pravidlá (content checks the XSD cannot perform)
    # ------------------------------------------------------------------
    # Source: Poučenie na vyplnenie kontrolného výkazu k DPH (FS SR) + zákon
    # č. 222/2004 Z. z. § 78a. Each detail row of A.1 / A.2 / B.1 / B.2 / C.1 /
    # C.2 carries základ dane (stĺpec 4), suma dane (stĺpec 5) and sadzba dane
    # (stĺpec 6); per the poučenie the suma dane is the daň pri danej sadzbe,
    # i.e. suma dane ≈ základ × sadzba/100 (príklad v poučení: 100,53 × 20 %
    # ≈ 20,11). The XSD only checks data types, not this content relation.
    #
    # NB: the official KV eForm (form.374.html) does NOT validate this
    # arithmetic — it only checks that the sadzba is a permitted value and that
    # suma dane / sadzba are present when a row is filled (the daň is "ako je
    # uvedená na faktúre"). So this is OUR advisory check beyond the portal,
    # hence severity 'warning' (rounding / §65–§66 margin / súhrnné faktúry).
    _KV_RATE_ABS_TOL = 0.02   # cent-level invoice rounding
    _KV_RATE_REL_TOL = 0.001  # absorbs súhrnné faktúry aggregating several lines

    def _check_summary_no_tax(self, code, row, out):
        """KV_NO_TAX for an aggregated section, which carries totals only.

        Cannot name a document the way the detail branch does — a summary row
        IS the collapse of many — so it names the section and the amount, which
        is what the filer has to go on here.
        """
        if "total_tax_base" not in row._fields:
            return
        base = row.total_tax_base or 0.0
        tax = row.total_tax_amount or 0.0
        if base and not tax and not code.startswith(("A.2", "C")):
            out.append({
                "code": "KV_NO_TAX", "severity": "error",
                "desc": "%s: základ bez sumy dane" % code,
                "detail": "%s: súhrnný základ %.2f, suma dane 0.00 — "
                          "skontrolujte doklady zahrnuté v tomto oddiele"
                          % (code, base)})

    def check_kontroly(self):
        """Return ``[{code, severity, desc, detail}]`` — empty = clean.

        ``severity='error'`` blocks export (the výkaz would be rejected/wrong);
        ``'warning'`` is logged (legitimate edge cases exist, e.g. §65/§66
        margin schemes report suma dane '0', súhrnné faktúry aggregate rows).
        """
        self.ensure_one()
        out = []
        for code, rows in self._collect_sections_by_code().items():
            for row in rows:
                if "tax_rate" not in row._fields:
                    # Summary / reconciliation section (SK B.3.1, CZ A.5/B.3):
                    # no rate and no per-document reference, so KV_RATE cannot
                    # apply — but the base/tax pair still exists as a total,
                    # and a total base filed against a zero total tax is the
                    # same undescribable supply KV_NO_TAX exists to stop, just
                    # aggregated. Skipping the whole row let exactly that
                    # through the one check written for it.
                    self._check_summary_no_tax(code, row, out)
                    continue
                rate = row.tax_rate or 0.0
                base = row.tax_base_amount or 0.0
                tax = row.tax_amount or 0.0
                # rate-band equality: only where a rate and a tax are present
                # (skips A.2 base-only reverse-charge rows and §65/§66 '0' rows)
                if rate and tax:
                    expected = base * rate / 100.0
                    tol = self._KV_RATE_ABS_TOL + self._KV_RATE_REL_TOL * abs(base)
                    if abs(tax - expected) > tol:
                        # ⚠️ Severity by MAGNITUDE, not one level for every
                        # disagreement. A cent off the arithmetic is a rounding
                        # question and warning is right; a tax several times
                        # the rate is not a tolerance question at all, and
                        # shipping it as a warning means the check ran,
                        # disagreed, and the document went out anyway.
                        #
                        # Measured: an A.1 row filed 5 147.10 of VAT against an
                        # arithmetic 458.85 — 12.9x — in a schema-valid
                        # document, in a month that reported green, because
                        # every KV_RATE was a warning. The row was wrong for a
                        # reason worth blocking on: a tag resolved to twelve
                        # taxes and their rates were summed.
                        #
                        # A factor of two is far outside any rounding or
                        # aggregation effect these tolerances exist for, so it
                        # is an error and stops the export.
                        ratio = abs(tax) / abs(expected) if expected else 0.0
                        gross = ratio >= 2.0 or ratio <= 0.5
                        out.append({
                            "code": "KV_RATE",
                            "severity": "error" if gross else "warning",
                            "desc": "%s: suma dane = základ × sadzba/100" % code,
                            "detail": "základ %.2f × %g%% = %.2f, uvedené %.2f"
                                      % (base, rate, expected, tax)})
                # ⚠️ A BASE THAT REPORTS NO TAX IS THE CASE `KV_RATE` CANNOT
                # SEE. It guards on `rate and tax`, so a zero tax reads as
                # "nothing to check" rather than "off by a factor", and the
                # magnitude grading never gets the chance to grade it.
                #
                # That is not hypothetical and it was a REGRESSION of this
                # module's own making: narrowing the tax set stopped a row
                # being filed at 258 % of its base and left it filed at zero
                # instead — and where the old behaviour was wrong AND warned,
                # the new one was wrong and silent. The previous state was more
                # visible, which is the wrong direction to move in.
                #
                # A taxable supply with a base and no tax cannot be described,
                # so it cannot be filed: this is an error, not a warning. The
                # rate is deliberately not required to be present — a row whose
                # rate could not be determined reports none, and that is
                # precisely the row this must catch.
                if base and not tax and not code.startswith(("A.2", "C")):
                    out.append({
                        "code": "KV_NO_TAX", "severity": "error",
                        "desc": "%s: základ bez sumy dane" % code,
                        # Name the DOCUMENT, as every other kontrola does. An
                        # amount is the harder handle on a month with several
                        # rows, and the point of a named check is that somebody
                        # can go and open the thing it names.
                        "detail": "%s: základ %.2f, suma dane 0.00 — sadzbu sa "
                                  "nepodarilo určiť z dokladu; doplňte daň na "
                                  "riadok dokladu" % (
                                      row.entry_ref or _("(bez čísla)"), base)})
                # sign consistency on the non-correction sections (A/B): základ
                # and daň must share sign (C.1/C.2 hold signed opravy — skipped)
                if not code.startswith("C") and base and tax and (base > 0) != (tax > 0):
                    out.append({
                        "code": "KV_SIGN", "severity": "warning",
                        "desc": "%s: základ a suma dane majú mať rovnaké znamienko" % code,
                        "detail": "základ %.2f, suma dane %.2f" % (base, tax)})
        return out

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx["sections_by_code"] = self._collect_sections_by_code()
        return ctx

    def _collect_sections_by_code(self):
        """Country modules override to return ``{code: recordset}``."""
        return {}

    def _cssk_comparable_rows(self):
        """Per-DOCUMENT comparison, section by section.

        A control statement is not a list of boxes. § 78a reports individual
        invoices, and a discrepancy is about a document — which is why this
        answers with the invoice rather than with a figure: an accountant
        chasing a KV mismatch needs the doklad, not the delta.

        Identity and figures are the form's OWN — ``_kv_identity`` says what
        makes two rows the same document across statements and ``_kv_values``
        what makes it changed, both of which the dodatočný delta already
        computes. Reusing them is deliberate: a second notion of "the same
        row" in one module drifts from the first, and comparison and delta
        disagreeing about identity would be worse than either being wrong.
        """
        self.ensure_one()
        sections = self._collect_sections_by_code()
        if not sections:
            return None
        out = {}
        for code, rows in sections.items():
            for row in rows:
                if "_kv_identity" not in dir(row):
                    continue
                identity = row._kv_identity()
                # A section CAN legitimately hold two rows of one identity
                # (the same invoice at two rates in a section that does not
                # carry the rate). Keep both by making the ordinal part of the
                # key rather than letting one overwrite the other.
                key = (code, identity)
                seq = 1
                while key in out:
                    seq += 1
                    key = (code, identity + ("#%d" % seq,))
                out[key] = row._kv_values()
        return out
