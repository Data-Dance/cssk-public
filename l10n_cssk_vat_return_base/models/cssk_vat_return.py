from odoo import _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_lt = LazyTranslate(__name__)


class CSSKVatReturn(models.Model):
    """VAT return (daňové priznanie k DPH / DPHDP3).

    Each line is a signed sum of tax-tagged move-line balances, or an aggregate
    over other lines. CE-clean: uses ``account.account.tag._get_tax_tags`` (CE)
    rather than the EE report engine.
    """

    _name = "cssk.vat.return"
    _description = "VAT Return"
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
        "cssk.vat.return.version",
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
        "cssk.vat.return.type",
        domain="[('version_id', '=', version_id)]",
        required=True,
    )

    line_ids = fields.One2many(
        "cssk.vat.return.line", "return_id",
        copy=True)  # carry manual overrides (carryover lines) onto an amendment

    # Health roll-up: drillable leaves that don't tie to their journal items.
    unreconciled_count = fields.Integer(compute="_compute_unreconciled_count")

    @api.depends("line_ids.has_source", "line_ids.source_reconciles")
    def _compute_unreconciled_count(self):
        for ret in self:
            ret.unreconciled_count = len(ret.line_ids.filtered(
                lambda ln: ln.has_source and not ln.source_reconciles))

    def action_view_unreconciled(self):
        self.ensure_one()
        bad = self.line_ids.filtered(
            lambda ln: ln.has_source and not ln.source_reconciles)
        return {
            "type": "ir.actions.act_window",
            "name": _("Unreconciled rows"),
            "res_model": "cssk.vat.return.line",
            "view_mode": "list",
            "domain": [("id", "in", bad.ids)],
            "context": {"create": False, "delete": False},
        }

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
        "cssk.vat.return", string="Amends", copy=False, readonly=True, index=True,
        help="The originally-filed return this amended / corrective return amends.")
    amendment_ids = fields.One2many(
        "cssk.vat.return", "original_return_id", string="Amendments")
    discovery_date = fields.Date(
        string="Difference identification date",
        help="Date the fact giving rise to the amended return was identified "
             "(datumZisteniaDdp); mandatory for an amended return.")

    # --- § 79 nadmerný odpočet carry-forward (settlement / UHRADIT) ----------
    # The official form lines (own tax liability / excess deduction — e.g. SK
    # r32 / r33) are gross per-period values. The amount actually PAID/REFUNDED
    # (the filing header, MRP's UHRADIT) nets a § 79 carry: an excess that is
    # not refunded is carried to the next period and offsets its daň. Model it
    # explicitly so to_pay matches the header across periods:
    #     to_pay = own_tax − excess − excess_carried_in + excess_carried_out
    # with each period's carried_out feeding the next period's carried_in.
    # WHICH lines carry the own tax / excess is version DATA
    # (own_tax_line_code / excess_line_code on the version record), not
    # hardcoded form knowledge; without the codes the settlement is inert
    # (to_pay = 0).
    excess_carried_in = fields.Monetary(
        currency_field="currency_id", default=0.0, copy=False,
        string="Excess deduction from prior period",
        help="Excess deduction carried IN from a prior period to offset this "
             "period's own tax liability (§ 79). Use 'Carry excess deduction' "
             "to pull it from the prior return, or set it manually.")
    excess_carried_out = fields.Monetary(
        currency_field="currency_id", default=0.0, copy=False,
        string="Excess deduction to carry forward",
        help="The part of THIS period's excess deduction not refunded but "
             "carried OUT to the next period (§ 79 election — the remainder is "
             "refunded). Becomes the next return's 'from the previous period'.")
    prior_return_id = fields.Many2one(
        "cssk.vat.return", string="Previous period", copy=False,
        help="Return of the immediately-preceding tax period — source of the "
             "carried-in excess.")
    to_pay = fields.Monetary(
        compute="_compute_to_pay", store=True, currency_field="currency_id",
        string="To pay / (refund)",
        help="Settlement after the § 79 carry = own tax − excess deduction "
             "− carried_in + carried_out (line codes from the version). "
             "Positive = tax to pay; negative = excess deduction to refund. "
             "Matches the filing header (UHRADIT).")

    @api.depends("line_ids.value", "line_ids.code",
                 "excess_carried_in", "excess_carried_out",
                 "version_id.own_tax_line_code", "version_id.excess_line_code")
    def _compute_to_pay(self):
        for ret in self:
            own_code = ret.version_id.own_tax_line_code
            excess_code = ret.version_id.excess_line_code
            if not own_code or not excess_code:
                # The version declares no settlement lines → nothing to
                # settle (graceful: no crash, no half-computed figure).
                ret.to_pay = 0.0
                continue
            vals = {line.code: line.value for line in ret.line_ids}
            net = (vals.get(own_code, 0.0) - vals.get(excess_code, 0.0)
                   - ret.excess_carried_in + ret.excess_carried_out)
            ret.to_pay = ret.currency_id.round(net) if ret.currency_id else net

    @api.constrains("excess_carried_in", "excess_carried_out")
    def _check_carry(self):
        for ret in self:
            if ret.excess_carried_in < 0 or ret.excess_carried_out < 0:
                raise ValidationError(_(
                    "Prenášaný nadmerný odpočet nemôže byť záporný."))
            excess_code = ret.version_id.excess_line_code
            if not excess_code or not ret.line_ids:
                continue
            excess = {line.code: line.value
                      for line in ret.line_ids}.get(excess_code, 0.0)
            if ret.excess_carried_out > excess + 0.01:
                raise ValidationError(_(
                    "Nadmerný odpočet na prenos (%(out).2f) nemôže byť vyšší "
                    "ako nadmerný odpočet obdobia %(code)s (%(excess).2f).",
                    out=ret.excess_carried_out, code=excess_code,
                    excess=excess))

    def _find_prior_return(self):
        """The immediately-preceding return, as the § 79 carry source.

        Historical filings are excluded. A legacy record states what was
        submitted for a period that predates this system; letting one answer
        "the previous period" would feed a migrated figure into a live
        settlement, and ``excess_carried_out`` on it is whatever the migration
        put there rather than an election this company made here. The carry is
        pulled from a return this system produced, or from nothing.
        """
        self.ensure_one()
        return self.search([
            ("company_id", "=", self.company_id.id),
            ("country_id", "=", self.country_id.id),
            ("date_to", "<", self.date_from),
            ("state", "!=", "cancelled"),
            ("legacy", "=", False),
            ("id", "!=", self.id),
        ], order="date_to desc", limit=1)

    def action_pull_prior_carry(self):
        """Carry the prior period's unrefunded excess into this return."""
        for ret in self:
            prior = ret.prior_return_id or ret._find_prior_return()
            if not prior:
                raise UserError(_(
                    "Nenašlo sa predchádzajúce daňové priznanie, z ktorého by "
                    "sa dal preniesť nadmerný odpočet."))
            ret.prior_return_id = prior
            ret.excess_carried_in = prior.excess_carried_out
        return True

    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for ret in self:
            ret.name = "DPH %s — %s" % (
                ret.date_from or "",
                ret.date_to or "",
            )

    # ------------------------------------------------------------------
    # Compute (the evaluator)
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only draft returns can be recomputed."))
        # Preserve manual overrides across the recompute. An overridden line's
        # value is taken from manual_value and fed into the computed dict, so
        # dependent aggregate lines see it too (e.g. r35 = r32 - r34).
        overrides = {
            line.code: line.manual_value
            for line in self.line_ids
            if line.is_overridden
        }
        self.line_ids.unlink()
        # Resolved once and shared with every line's drill-down domain below,
        # so the figure and the list it drills into cannot come from different
        # period selections.
        period_move_ids = self._cssk_period_move_ids(
            self.company_id, self.date_from, self.date_to)
        move_lines = self._period_move_lines(period_move_ids)
        computed = {}
        vals = []
        for ldef in self.version_id.line_def_ids.sorted("sequence"):
            overridden = ldef.code in overrides
            src_domain = []
            if overridden:
                value = overrides[ldef.code]
            elif ldef.kind == "tags":
                value = self._eval_tags(
                    ldef.tag_formula, move_lines, ldef.line_filter)
                src_domain = self._tag_source_domain(
                    ldef.tag_formula, period_move_ids)
            elif ldef.kind == "aggregate":
                value = self._eval_aggregate(ldef.aggregate_formula, computed)
            else:  # manual without an override
                value = 0.0
            computed[ldef.code] = value
            vals.append(
                {
                    "return_id": self.id,
                    "code": ldef.code,
                    "name": ldef.name,
                    "sequence": ldef.sequence,
                    "value": value,
                    "kind": ldef.kind,
                    "manual_value": value if overridden else 0.0,
                    "is_overridden": overridden,
                    "source_domain": repr(src_domain),
                    "formula_note": (
                        ldef.aggregate_formula if ldef.kind == "aggregate"
                        else (_("manual input") if ldef.kind == "manual" else "")),
                }
            )
        self.env["cssk.vat.return.line"].create(vals)
        self.state = "preview"

    def _period_move_lines(self, move_ids=None):
        """Tagged move lines in this return's period.

        Period selection lives on the shared statutory mixin so that the VAT
        return, the control statement and the EC sales list cannot drift apart
        on what "the period" means.
        """
        self.ensure_one()
        if move_ids is None:
            move_ids = self._cssk_period_move_ids(
                self.company_id, self.date_from, self.date_to
            )
        if not move_ids:
            return self.env["account.move.line"]
        return self.env["account.move.line"].search([
            ("parent_state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            ("tax_tag_ids", "!=", False),
            ("move_id", "in", move_ids),
        ])

    @staticmethod
    def _iter_tag_terms(formula):
        """Yield ``(sign, tag_name)`` for each term of a tag formula.

        ONE parser for the grammar, because two read it: ``_eval_tags``
        computes the figure and ``_tag_source_domain`` re-queries the
        drill-down, and a return whose drill-down disagrees with its own figure
        is worse than either being wrong alone. They had drifted — the domain
        spelled the per-term sign as ``.replace("+", "|")``, which turns
        ``-24|+24_PR`` into the right tags by accident and ``+24|-24_PR`` into
        ``_get_tax_tags("-24_PR")``, a literal minus that matches nothing.

        Grammar: terms are separated by ``|``; a leading ``+``/``-`` on the
        FORMULA is its sign, and a term may override it with its own (see
        ``_eval_tags`` for why § 25 needs that).
        """
        formula = (formula or "").strip()
        if not formula:
            return
        sign = -1.0 if formula.startswith("-") else 1.0
        for term in formula.lstrip("+-").split("|"):
            term = term.strip()
            if not term:
                continue
            # An unsigned term inherits the formula's sign, so every existing
            # definition keeps its meaning exactly.
            term_sign = sign
            if term[0] in "+-":
                term_sign = -1.0 if term[0] == "-" else 1.0
                term = term[1:].strip()
            if term:
                yield term_sign, term

    def _cssk_tag_line_filter(self, key, lines):
        """Narrow a kind=tags line's move lines by a country-specific rule.

        The base answer is "no rule", so a line with no ``line_filter`` — every
        line of every current form — behaves exactly as it always did. A
        country module overrides this for a split its chart cannot express as
        a tag; see ``l10n_sk_vat_return`` and § 69 ods. 3.

        An UNRECOGNISED key must raise rather than quietly return everything:
        a filter that silently stops filtering puts the whole of one row onto
        another and the return still foots.
        """
        raise UserError(_(
            "Line filter %r is not implemented for this country. A form line "
            "asking for a restriction nobody applies would report the whole "
            "of its tags instead of its share of them.", key))

    def _eval_tags(self, formula, move_lines, line_filter=None):
        """Signed sum of balances of move lines carrying the formula's tag.

        Sign contract (Odoo 19): tax tags are UNSIGNED and lines carry no
        per-line invert flag (``tax_tag_invert`` was removed in 18.5 — see
        ``upgrade_code/18.5-00-no-tax-tag-invert.py``); the core tax_tags
        report engine sums RAW signed balances and applies only the
        formula-level '-' sign, which is exactly what this method does. Manual
        misc-journal entries therefore aggregate identically to invoices —
        do NOT add any per-line inversion on top.
        """
        formula = (formula or "").strip()
        if not formula:
            return 0.0

        # SEVERAL tags may feed one line: "09|09a|09b". The sign is the
        # formula's and applies to the whole set.
        #
        # This is how a form VINTAGE is expressed. A line that a later form
        # splits by rate is one line in the earlier form, and the earlier
        # version's definition says so by collecting every tag the split
        # produced. The Slovak reverse charge is the case: ``r09`` alone until
        # 1. 7. 2025, then ``r09``/``r09a``/``r09b`` by rate.
        #
        # It is needed because a tag lives on the TAX and a line belongs to a
        # PERIOD. Where a rate spans the change — 23 % ran from 1. 1. 2025 and
        # the form changed on 1. 7. — the same tax is filed on ``r09`` for six
        # months and ``r09b`` for the next six, and no property of the tax can
        # say which. Remapping the tax's tags cannot express it either: there
        # is one tax and two answers. The version can, because the version IS
        # the period.
        # A TERM may carry its own sign, and a line that collects both sides of
        # one statutory quantity needs it: "-24|+24_PR".
        #
        # The grid's convention is uniform and is what decides this — every
        # SUPPLIED base line is negative (r01 '-01', r03 '-03', r13 '-13') and
        # every RECEIVED one is positive (r09 '09', r11 '11', r18 '18|18a'),
        # because a revenue base is a credit and an expense base a debit, and
        # the form wants both as the same sign. A line collecting both sides
        # therefore cannot have one sign.
        #
        # § 25 is that line: `l10n_sk` splits the base correction into `24` on
        # the domestic sale rates and `24_PR` on the reverse-charge ones, while
        # the tax side is a single tag `25`. Sharing the formula's '-' across
        # both made the magnitude right and the sign wrong — measured on a
        # filed return, 2024-12 r24 read +190.80 against a filed −190.80.
        total = 0.0
        Tag = self.env["account.account.tag"]
        for term_sign, term in self._iter_tag_terms(formula):
            tags = Tag._get_tax_tags(term, self.country_id.id)
            if not tags:
                continue
            matched = move_lines.filtered(lambda l: l.tax_tag_ids & tags)
            if line_filter:
                matched = self._cssk_tag_line_filter(line_filter, matched)
            total += term_sign * sum(matched.mapped("balance"))
        return total

    def _tag_source_domain(self, formula, move_ids=None):
        """A serialisable domain for the move lines a ``kind=tags`` line
        aggregates (those carrying the formula's tax tag) — re-queried on
        drill-down rather than storing the line ids.

        The PERIOD is carried as the move ids ``_cssk_period_move_ids``
        selected, not as a date range, because those are not the same set. That
        helper reports output by tax point and input by deduction date, so a
        document whose supply and booking fall on opposite sides of a period
        boundary — routine in SK, and on CZ imports — belongs to a period its
        ``date`` does not name. Filtering the drill-down by ``date`` put such a
        document INSIDE the figure and OUTSIDE the list it drills into, which
        surfaces as ``source_reconciles`` false and paints a correctly-computed
        return red.

        ``move_ids`` is the caller's already-resolved period, passed in so a
        return with sixty tag lines resolves it once rather than sixty times.
        """
        self.ensure_one()
        formula = (formula or "").strip()
        if not formula:
            return []
        # Same grammar as ``_eval_tags``, through the same parser; drill-down
        # must show every line the figure was computed from, or the two
        # disagree.
        Tag = self.env["account.account.tag"]
        tags = Tag.browse()
        for _term_sign, name in self._iter_tag_terms(formula):
            tags |= Tag._get_tax_tags(name, self.country_id.id)
        if not tags:
            return []
        if move_ids is None:
            move_ids = self._cssk_period_move_ids(
                self.company_id, self.date_from, self.date_to)
        if not move_ids:
            return []
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("move_id", "in", list(move_ids)),
                ("tax_tag_ids", "in", tags.ids)]

    def _eval_aggregate(self, formula, computed):
        """Evaluate an aggregate formula over already-computed line codes."""
        if not formula:
            return 0.0
        return float(safe_eval(formula, dict(computed)) or 0.0)

    # ------------------------------------------------------------------
    # Export — the pipeline lives in cssk.statutory.submission.mixin;
    # only the form-specific hooks are parameterized here.
    # ------------------------------------------------------------------
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("VAT return")
    _cssk_xml_name_fallback = "vat_return"

    def _cssk_export_draft_error(self):
        return _("Compute the return before exporting.")

    def _cssk_check_kontroly(self):
        self.ensure_one()
        self._cssk_enforce_kontroly()
        return True

    # ------------------------------------------------------------------
    # kontrolné pravidlá (content checks the XSD cannot perform)
    # ------------------------------------------------------------------
    def _kontroly_rules(self):
        """Country modules override to return a list of rule dicts. Supported:

        * ``{'type': 'rate', 'base': code, 'tax': code, 'rates': [r, ...]}`` —
          the implied rate ``|tax| / |base| × 100`` must be (within tolerance)
          one of ``rates`` (statutory daň = základ × sadzba).
        * ``{'type': 'nonneg', 'code': code}`` — value must be ≥ 0.
        * ``{'type': 'exclusive', 'a': code, 'b': code}`` — not both > 0.
        * ``{'type': 'le', 'a': code, 'b': code}`` — ``a`` must be ≤ ``b``.
        """
        return []

    _KONTROLY_RATE_TOL = 0.5   # percentage-point tolerance (aggregation/rounding)
    _KONTROLY_EPS = 0.01

    def check_kontroly(self):
        """Return ``[{code, severity, desc, detail}]`` — empty = clean."""
        self.ensure_one()
        vals = {line.code: line.value for line in self.line_ids}
        out = []
        for rule in self._kontroly_rules():
            t = rule["type"]
            if t == "rate":
                base = vals.get(rule["base"], 0.0)
                tax = vals.get(rule["tax"], 0.0)
                if abs(base) < 1.0:
                    continue  # nothing meaningful to imply a rate from
                implied = abs(tax) / abs(base) * 100.0
                if min(abs(implied - r) for r in rule["rates"]) > self._KONTROLY_RATE_TOL:
                    out.append({
                        "code": "DPH_RATE", "severity": "warning",
                        "desc": "%s = %s × sadzba (%s)" % (
                            rule["tax"], rule["base"],
                            "/".join("%g%%" % r for r in rule["rates"])),
                        "detail": "implikovaná sadzba %.2f %% (základ %.2f, daň %.2f)"
                                  % (implied, base, tax)})
            elif t == "nonneg":
                if vals.get(rule["code"], 0.0) < -self._KONTROLY_EPS:
                    out.append({
                        "code": "DPH_SIGN", "severity": "error",
                        "desc": "%s musí byť ≥ 0" % rule["code"],
                        "detail": "%.2f" % vals.get(rule["code"], 0.0)})
            elif t == "exclusive":
                a, b = vals.get(rule["a"], 0.0), vals.get(rule["b"], 0.0)
                if a > self._KONTROLY_EPS and b > self._KONTROLY_EPS:
                    out.append({
                        "code": "DPH_EXCL", "severity": "error",
                        "desc": "%s a %s sa vylučujú" % (rule["a"], rule["b"]),
                        "detail": "%s=%.2f, %s=%.2f" % (rule["a"], a, rule["b"], b)})
            elif t == "le":
                a, b = vals.get(rule["a"], 0.0), vals.get(rule["b"], 0.0)
                if a > b + self._KONTROLY_EPS:
                    out.append({
                        "code": "DPH_LE", "severity": "error",
                        "desc": "%s nesmie byť vyšší ako %s" % (rule["a"], rule["b"]),
                        "detail": "%s=%.2f, %s=%.2f" % (rule["a"], a, rule["b"], b)})
        return out

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx.update({
            "lines": self.line_ids,
            "values": {line.code: line.value for line in self.line_ids},
            # formatted strings keyed by code; '' for codes not computed
            "values_fmt": {
                line.code: "%.2f" % line.value for line in self.line_ids
            },
        })
        return ctx


class CSSKVatReturnLine(models.Model):
    _name = "cssk.vat.return.line"
    _description = "VAT Return Line"
    _order = "return_id, sequence, code"

    return_id = fields.Many2one(
        "cssk.vat.return", required=True, ondelete="cascade", index=True
    )
    company_currency_id = fields.Many2one(related="return_id.currency_id")
    code = fields.Char(required=True)
    name = fields.Char()
    sequence = fields.Integer(default=10)
    kind = fields.Selection(
        [("tags", "Tax tags"), ("aggregate", "Aggregate"), ("manual", "Manual")],
        help="Line kind from the version definition (informational).",
    )
    value = fields.Monetary(
        currency_field="company_currency_id",
        help="Effective value: the computed result, or the manual override.",
    )
    is_overridden = fields.Boolean(
        string="Override",
        help="Tick to enter a manual value for this line — used for carryover "
        "/ external lines (registration deduction, traveller refunds, excess "
        "offset, amended-return differences) and to correct a computed line. "
        "The value is preserved and fed into dependent lines on recompute.",
    )
    manual_value = fields.Monetary(
        currency_field="company_currency_id",
        help="Manual value applied when 'Override' is ticked.",
    )

    # --- drill-down: the journal items behind a tag-based (leaf) line ---
    is_leaf = fields.Boolean(compute="_compute_is_leaf", store=True)
    # Tier-3 transparency: for aggregate/derived rows that have no single line
    # set, show how the value was obtained (the formula / "manual input").
    formula_note = fields.Char(string="Derivation")
    # Drill-down: stored as a small serialised domain, re-queried on click.
    source_domain = fields.Char()
    has_source = fields.Boolean(compute="_compute_has_source")
    source_reconciles = fields.Boolean(compute="_compute_source_reconciles")

    @api.depends("kind")
    def _compute_is_leaf(self):
        for line in self:
            line.is_leaf = line.kind == "tags"

    @api.depends("source_domain")
    def _compute_has_source(self):
        for line in self:
            line.has_source = bool(line.source_domain
                                   and line.source_domain not in ("[]", "False"))

    @api.depends("source_domain", "value")
    def _compute_source_reconciles(self):
        # Batched: ONE move-line fetch per return (instead of one _read_group
        # per line on every form load). All leaf domains of a return share
        # the period/company base and differ only in their tag set, so fetch
        # the union once and intersect per line in Python — same any-tag
        # `in` semantics as the per-line domain (a move line carrying two of
        # a line's tags still counts once).
        AML = self.env["account.move.line"]
        for lines in self.grouped("return_id").values():
            pending = []   # (line, tag_id_set, base_domain_key, base_domain)
            for line in lines:
                if not line.has_source:
                    line.source_reconciles = False
                    continue
                domain = safe_eval(line.source_domain)
                tag_ids = set()
                base = []
                for term in domain:
                    if (isinstance(term, (list, tuple))
                            and term[0] == "tax_tag_ids"):
                        ids = term[2]
                        tag_ids.update(
                            ids if isinstance(ids, (list, tuple)) else [ids])
                    else:
                        base.append(
                            list(term) if isinstance(term, (list, tuple))
                            else term)
                pending.append((line, tag_ids, repr(base), base))
            by_base = {}
            for entry in pending:
                by_base.setdefault(entry[2], []).append(entry)
            for entries in by_base.values():
                union = set().union(*(tags for _, tags, _, _ in entries))
                mls = AML.search(
                    entries[0][3] + [("tax_tag_ids", "in", list(union))]
                ) if union else AML
                data = [(set(ml.tax_tag_ids.ids), ml.balance) for ml in mls]
                for line, tags, _, _ in entries:
                    s = sum(bal for ml_tags, bal in data if ml_tags & tags)
                    line.source_reconciles = (
                        abs(abs(s) - abs(line.value)) < 0.5)

    def action_view_source_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "l10n_cssk_vat_return_base.view_move_line_dph_audit",
            raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": _("Source documents — %s %s") % (
                self.code or "", self.name or ""),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": [(view.id if view else False, "list"), (False, "form")],
            "domain": safe_eval(self.source_domain or "[]"),
            "context": {"create": False, "delete": False,
                        "group_by": ["move_id"]},
        }

    @api.onchange("is_overridden", "manual_value")
    def _onchange_override(self):
        # Immediate feedback on this line; dependent aggregates update on
        # the next Compute.
        for line in self:
            if line.is_overridden:
                line.value = line.manual_value
