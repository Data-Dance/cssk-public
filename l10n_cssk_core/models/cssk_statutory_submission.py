# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared submission/retention mixin for statutory filings.

Adds the "filed copy is durable" guarantees on top of the draft → preview →
exported → submitted state machine that each statutory statement already has:

* ``action_submit`` freezes the exported XML as the **filed copy**
  (``submitted_attachment_id``), stamps the filing date/reference and locks the
  record;
* a submitted record cannot be re-exported or recomputed (its concrete
  ``action_export_xml`` calls ``_ensure_not_submitted`` first);
* ``action_reset_to_draft`` is the explicit unlock — it keeps the filed copy so
  the originally-submitted XML is never lost (needed e.g. as the "posledná známa
  daň" baseline for a dodatočné priznanie); it is gated on the Accounting /
  Administrator group;
* every submitted XML is additionally accumulated in ``filed_history_ids``, so
  after a reset → recompute → resubmit cycle the ORIGINALLY-filed copy stays
  reachable (``submitted_attachment_id`` is only the latest);
* a record in state ``submitted`` cannot be deleted (reset it first).

The concrete model must define ``state`` (with a ``submitted`` value) and
``xml_attachment_id``; this mixin only adds the retention fields and actions.

Historical filings
------------------
``legacy`` and ``state == "legacy"`` are ONE fact written two ways, joined in
``create`` / ``write`` so they cannot come apart. The state is terminal and
**off** the workflow rather than at the end of it: a historical filing was
completed and submitted years ago by whoever ran the previous system, so no
transition leads into or out of it, and the only thing that may be done to one
is to compare it with what this system computes for the same period.

Two things it deliberately does NOT do:

* **It does not use ``submitted``**, though that is what these filings are.
  ``unlink`` refuses a submitted record and points at
  ``action_reset_to_draft``, which changes ``state`` and is therefore refused
  in turn by ``_cssk_check_not_legacy`` — so every materialised filing would
  be permanently undeletable, against an importer whose whole method is
  reload-and-remeasure.
* **It does not block deletion.** "Frozen" here means the record cannot be
  advanced, recomputed, exported or submitted — not that it cannot be removed
  and re-materialised, which is exactly what a re-import does.

Export pipeline
---------------
``action_export_xml`` is the ONE consolidated export orchestration (it used
to be duplicated per statement base with a diverging stage order):

    _ensure_not_submitted → state gate → _cssk_preflight_export →
    _cssk_check_kontroly (content checks, BEFORE rendering) → _render_xml →
    _validate_against_schema → _attach_xml → state = 'exported'

Kontrolné pravidlá deliberately run BEFORE rendering: they check the
statement's *content* (line values / rows), so a content error should fail
fast with a named rule instead of surfacing later as a cryptic XSD error —
and a template crash must never mask a content violation.

The statement bases parameterize the shared pipeline through small hooks:
``_cssk_form_label`` / ``_cssk_xml_name_fallback`` (messages / attachment
name), ``_cssk_export_draft_error`` (state-gate wording),
``_cssk_render_context`` (extra QWeb variables) and ``_cssk_check_kontroly``
(default no-op — bases/country modules override; ``_cssk_enforce_kontroly``
is the shared severity-aware runner for ``check_kontroly()`` results).
"""
import base64
import logging
import re

from lxml import etree
from markupsafe import Markup

from psycopg2 import IntegrityError

from odoo import Command, _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError, ValidationError

_lt = LazyTranslate(__name__)

_logger = logging.getLogger(__name__)


class CSSKStatutorySubmissionMixin(models.AbstractModel):
    _name = "cssk.statutory.submission.mixin"
    _description = "Statutory filing submission / retention"

    # Parameterization of the shared export pipeline (per concrete model).
    # Interpolated into user-facing messages / the attachment filename.
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("statement")
    _cssk_xml_name_fallback = "statement"

    submitted_date = fields.Datetime(readonly=True, copy=False)
    submission_reference = fields.Char(
        copy=False,
        help="Submission identifier / confirmation number from the FS portal.")
    submitted_attachment_id = fields.Many2one(
        "ir.attachment", string="Filed XML", readonly=True, copy=False,
        help="The exact XML that was submitted; preserved across reset-to-draft.")
    filed_history_ids = fields.Many2many(
        "ir.attachment", string="Filed history", readonly=True, copy=False,
        help="Every XML that was ever marked submitted for this filing. "
             "'Filed XML' is the latest one; after a reset → recompute → "
             "resubmit cycle the previously-filed copies stay reachable here.")

    # ------------------------------------------------------------------
    # historical (legacy) filings
    # ------------------------------------------------------------------
    legacy = fields.Boolean(
        string="Historical filing", readonly=True,
        # ⚠️ copy=False is LOAD-BEARING. ``action_create_amendment`` builds the
        # amendment with ``self.copy()``, and an Odoo Boolean copies by
        # default — so without this the dodatočné raised against a historical
        # period would itself come out legacy: not submittable, not
        # recomputable, and useless for the one thing it exists to do. A
        # legacy record is amendable ON PURPOSE; only the record itself is
        # frozen, never its amendment.
        copy=False,
        help="This filing was not produced here — it records what was actually "
             "submitted for a period that predates this system, loaded from a "
             "migration. It is a historical fact, so it can never be exported, "
             "submitted or recomputed, and it is invisible to anything that "
             "looks for 'the return of the previous period'. It CAN be "
             "amended: a dodatočné filed later against a historical period is "
             "an ordinary submittable return.\n\n"
             "Setting this puts the record in state 'Historical filing', which "
             "is terminal — the two are written together and cannot come "
             "apart.")
    legacy_source = fields.Char(
        string="Source system", readonly=True, copy=False,
        help="Where the filing came from, e.g. 'PREMIER', 'Money S4', 'i6', "
             "'MRP' — or how it was captured if by hand.")
    legacy_stated_codes = fields.Char(
        string="Rows the source states", readonly=True, copy=False,
        help="The row codes the source system's own filing could carry, "
             "comma-separated, written by the migration that materialised "
             "this record.\n\n"
             "A source rarely stores the form: PREMIER keeps ten summary "
             "figures where the Slovak priznanie has thirty-seven rows. Every "
             "row it cannot state is missing here for a structural reason, "
             "not because the filing omitted it — so the comparison reports "
             "those rows as informational instead of as differences. Left "
             "empty, every row is treated as one the source could have "
             "stated, which is the right reading of a filing captured by "
             "hand.")
    legacy_reference = fields.Char(
        string="Source reference", readonly=True, copy=False,
        help="Identifier of the import batch or source document this filing "
             "was materialised from, so a figure can be traced back to what "
             "produced it.")

    def _cssk_check_not_legacy(self, what):
        """Refuse *what* on a historical filing.

        Every one of these would destroy the only copy of what was actually
        submitted, which is the whole value of the record: recomputing
        overwrites the filed figures with ours, exporting and submitting would
        re-file a period that was filed years ago.
        """
        legacy = self.filtered("legacy")
        if legacy:
            raise UserError(_(
                "%(names)s %(verb)s a historical filing — a record of what was "
                "submitted, not a filing being made. It cannot be %(what)s. "
                "To correct the period, create an amendment (dodatočné) from "
                "it: the amendment is an ordinary return.",
                names=", ".join(legacy.mapped("display_name")),
                verb=_("are") if len(legacy) > 1 else _("is"),
                what=what,
            ))

    @staticmethod
    def _cssk_legacy_vals(vals):
        """Normalise the flag and the state onto each other, BOTH ways.

        Either one arriving alone implies the other, so whichever a caller
        happens to write, the pair stays whole. One direction would not be
        enough: the importer writes the flag, but a server action or a fixture
        is as likely to write the state.
        """
        if vals.get("legacy"):
            vals["state"] = "legacy"
        elif vals.get("state") == "legacy":
            vals["legacy"] = True
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        # Fresh dicts. A caller may hand the same dict to several creates, and
        # an override that edits one in place leaks into the others.
        return super().create(
            [self._cssk_legacy_vals(dict(vals)) for vals in vals_list])

    @api.constrains("legacy", "state")
    def _cssk_check_legacy_state_agree(self):
        """The flag and the state are one fact; refuse them disagreeing.

        ``create`` and ``write`` normalise the pair, but neither sees every
        way a value can arrive — ``default_legacy`` in the context is applied
        by ``create`` itself, after the override has read its vals, and a raw
        ``write({"legacy": False})`` clears the flag without naming a state.
        The normalisation is the convenience; this is the guarantee.
        """
        for rec in self:
            if bool(rec.legacy) != (rec.state == "legacy"):
                raise ValidationError(_(
                    "%(name)s is inconsistent: 'Historical filing' is %(flag)s "
                    "but its state is '%(state)s'. The flag and the state are "
                    "the same fact and are written together — to un-mark a "
                    "historical filing, set both.",
                    name=rec.display_name, flag=rec.legacy,
                    state=rec.state))

    def write(self, vals):
        # Setting the flag IS the transition, and the two are joined HERE so
        # that no caller can produce the one combination that means nothing —
        # a historical filing sitting in ``draft``. That combination is not
        # hypothetical: it is what every materialised filing did before this
        # existed, because the importer sets ``legacy`` and never touches
        # ``state``, so the default won. A list of 134 completed filings all
        # reading "Draft" tells an accountant the opposite of the truth, and a
        # ribbon on the form does not reach a list view.
        #
        # Joined in the localization rather than fixed in the importer on
        # purpose: the importer lives in another repository, and a rule split
        # across two repositories is a rule that drifts.
        vals = self._cssk_legacy_vals(dict(vals))
        if "state" in vals and vals["state"] != "legacy":
            # The state machine is the other way in. Blocked here rather than
            # only in the actions, because a filing can be moved by a server
            # action, an import or a stray write as easily as by a button.
            self._cssk_check_not_legacy(_("moved to another state"))
        return super().write(vals)

    # ------------------------------------------------------------------
    # comparing a historical filing against what this system computes
    # ------------------------------------------------------------------
    def _cssk_comparable_lines(self):
        """``{code: value}`` for comparison, or ``None`` if not comparable.

        Default: a form whose ``line_ids`` carry ``code`` and ``value``, which
        is the VAT return, the income-tax return and the financial statements.
        The control statement and the EC sales list report ROWS rather than
        coded lines and return ``None`` until each defines what comparing two
        of them means — an honest "cannot" beating a comparison of nothing.
        """
        self.ensure_one()
        lines = self._fields.get("line_ids") and self.line_ids
        if lines is None or "code" not in lines._fields or (
                "value" not in lines._fields):
            return None
        return {ln.code: ln.value for ln in lines if ln.code}

    def _cssk_comparable_rows(self):
        """``{(section, identity): {field: value}}``, or ``None``.

        The other shape a statutory form comes in. A VAT return is a list of
        CODED lines and diffs as a dict of codes; a control statement and an
        EC sales list are lists of DOCUMENTS and partners, where "the same
        row" is an invoice or a counterparty rather than a box number. Those
        override this; everything else leaves it ``None`` and is compared by
        code.

        Identity must be the form's OWN notion of sameness, not one invented
        here — see the KV implementation, which reuses the identity the
        dodatočný delta already computes. Two notions of "the same row" in one
        module is the defect that cost 47 rows of the účtovná závierka.

        Boundary worth stating: this compares OUR materialised rows. A source
        that files a figure and also carries its own per-document detail
        behind it marks that detail on the way in (``is_backing_detail`` on
        the importer's staging model) and must not materialise it as a row
        here — summed beside the figure it backs, it double-counts. That is
        the importer's job and nothing in this method can see it.
        """
        self.ensure_one()
        return None

    def _cssk_compare_to_computed(self):
        """Diff this (historical) filing against a fresh computation.

        Returns ``{comparable, reason, rows}``. For a coded form each row is
        ``{code, filed, computed, diff, status}``; for a row-based one, the
        same shape with ``code`` naming the section and identity and ``filed``
        / ``computed`` holding the row's figures. ``status`` is one of
        ``ok`` / ``differs`` / ``only_filed`` / ``only_computed`` either way,
        so a caller does not care which kind of form it was handed.

        Three things this does deliberately:

        * **Recomputes rather than reading another saved record.** A saved
          return's lines carry ``is_overridden`` / ``manual_value``, so
          comparing two stored returns can measure somebody's editing instead
          of this engine. The scratch record is computed here and destroyed.
        * **Separates "cannot compute" from "computes zero".** They are
          different facts and folding them together turns an unimportable
          period into a wall of differences. On one real migration 106 of 138
          filed periods had no imported ledger behind them at all — the
          majority case, not an edge.
        * **Compares the UNION of both sides' codes.** A line we produce and
          the filing does not is as interesting as the reverse, and only the
          union shows it — except where the source could not state the row at
          all (``legacy_stated_codes``), which is ``not_stated`` rather than a
          difference. On the first PREMIER agenda that distinction was 33 of
          57 review items: the source keeps ten summary figures and the form
          has thirty-seven rows, so every month reported the same three
          missing rows as findings.
        """
        self.ensure_one()
        filed = self._cssk_comparable_lines()
        rows_mode = filed is None
        if rows_mode:
            filed = self._cssk_comparable_rows()
        if filed is None:
            return {"comparable": False,
                    "reason": _("This form does not support comparison."),
                    "rows": []}
        if not self._cssk_period_move_ids(
                self.company_id, self.date_from, self.date_to):
            return {"comparable": False,
                    "reason": _(
                        "No accounting data exists for %(df)s – %(dt)s, so "
                        "there is nothing to compare against. This is not a "
                        "difference of zero — the period was never imported.",
                        df=self.date_from, dt=self.date_to),
                    "rows": []}
        scratch = self.copy({
            "legacy": False, "legacy_source": False, "legacy_reference": False,
            "state": "draft",
            "original_return_id": False,
        })
        try:
            scratch.action_compute_lines()
            computed = (scratch._cssk_comparable_rows() if rows_mode
                        else scratch._cssk_comparable_lines()) or {}
        finally:
            # Destroyed either way: a scratch filing left behind would be
            # indistinguishable from a real one for the period.
            scratch.unlink()
        rows = []
        for key in sorted(set(filed) | set(computed), key=self._cssk_compare_sort):
            a, b = filed.get(key), computed.get(key)
            detail = False
            if a is None and not self._cssk_source_states(key, rows_mode):
                status, diff = "not_stated", self._cssk_compare_magnitude(b)
            elif a is None:
                status, diff = "only_computed", self._cssk_compare_magnitude(b)
            elif b is None:
                status, diff = "only_filed", -self._cssk_compare_magnitude(a)
            elif rows_mode:
                # A row-based form compares a TUPLE of figures. Any of them
                # moving is a difference: an invoice re-rated at the same
                # total is not the same row, and the § 78a dispute is about
                # the document, not the sum.
                status = "ok" if self._cssk_rows_equal(a, b) else "differs"
                diff = (self._cssk_compare_magnitude(b)
                        - self._cssk_compare_magnitude(a))
                if status == "differs" and abs(diff) < 0.005:
                    # A row whose FIRST figure matches reads as a difference
                    # of 0.00 and says nothing — the rate, the deducted
                    # amount or the counterparty's own reference moved, and
                    # the screen showed a row with no delta and no reason.
                    detail = self._cssk_row_difference_detail(a, b)
            else:
                diff = b - a
                status = "ok" if abs(diff) < 0.005 else "differs"
            rows.append({"code": self._cssk_compare_label(key, rows_mode),
                         "filed": a, "computed": b, "detail": detail,
                         "diff": diff, "status": status})
        return {"comparable": True, "reason": "", "rows": rows}

    @staticmethod
    def _cssk_row_difference_detail(filed, computed):
        """Which of a row's figures moved, where the leading one did not.

        Row-based forms compare a tuple — for a KV section (base, tax, rate,
        deducted, the counterparty's reference) — and the difference column
        carries only the first of them. When that one matches, the row is
        reported with a delta of 0.00, which reads as "no difference" beside
        a state of "to review". This says what actually changed.
        """
        parts = []
        for index, (x, y) in enumerate(zip(filed or (), computed or ()), 1):
            same = (abs(float(x) - float(y)) < 0.005
                    if isinstance(x, (int, float))
                    and isinstance(y, (int, float))
                    else (x or "") == (y or ""))
            if not same:
                parts.append(_("figure %(n)s: filed %(filed)s, computed "
                               "%(computed)s", n=index, filed=x, computed=y))
        if not parts:
            return False
        return _("The row's leading amount agrees; %s.", "; ".join(parts))

    def _cssk_source_states(self, key, rows_mode):
        """Could the source this filing came from carry this row at all?

        Only a historical filing whose migration said so answers no. Anything
        else — a filing produced here, one captured by hand, a migration that
        wrote no list — answers yes, so a row it lacks stays the finding it
        has always been.

        Row-based forms (the control statement, the EC sales list) are keyed
        by document or partner rather than by box number, and a source that
        states the section states whatever rows it has. So the question only
        applies to coded forms.
        """
        self.ensure_one()
        if rows_mode or not self.legacy or not self.legacy_stated_codes:
            return True
        stated = {c.strip() for c in self.legacy_stated_codes.split(",")}
        return str(key) in stated

    @staticmethod
    def _cssk_compare_sort(key):
        return tuple(str(part) for part in key) if isinstance(key, tuple) else (
            str(key),)

    @staticmethod
    def _cssk_compare_label(key, rows_mode):
        if not rows_mode:
            return key
        section, identity = key
        return "%s %s" % (section, " / ".join(
            str(part) for part in identity if part not in (None, "")))

    @staticmethod
    def _cssk_compare_magnitude(values):
        """The one figure that stands for a row, for the difference column.

        The FIRST of a row's values by convention — the base for a control
        statement, the reported hodnota for an EC sales list. It exists so a
        reader has something to sort by; the status is decided by the whole
        tuple, not by this.
        """
        if values is None:
            return 0.0
        if isinstance(values, (int, float)):
            return float(values)
        numeric = [v for v in values if isinstance(v, (int, float))]
        return float(numeric[0]) if numeric else 0.0

    @staticmethod
    def _cssk_rows_equal(a, b):
        if a is None or b is None:
            return False
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                if abs(float(x) - float(y)) >= 0.005:
                    return False
            elif (x or "") != (y or ""):
                return False
        return True

    def _cssk_collapse_unmapped(self, bad, agreeing=0):
        """A filing that matches NOT ONE row is one fact, not N differences.

        When the filed side and the computed side share no row code at all,
        their vocabularies do not line up — the filing is staged under names
        nobody has mapped yet — and every row we compute becomes a difference
        the filing "lacks". Each such row is true on its own and the set of
        them says something false: that we found forty problems in this
        period, rather than one.

        It is not a small effect. On the first real agenda, 1 292 of 1 294
        recorded discrepancies were one-sided rows of exactly this kind, and
        they buried the two that were real. An accountant opening that list
        cannot tell which two matter, which makes the list worse than nothing.

        So: no overlap at all collapses to a single row naming the count and a
        few examples. Any overlap whatsoever and every difference is reported
        individually, because then the vocabularies DO line up and a one-sided
        row is a genuine finding — a line the filing omitted, or one we
        produce that it never had.

        ⚠️ ``agreeing`` is the count of ``ok`` rows and is NOT optional in
        practice. ``bad`` has already had them filtered out, so the only
        evidence of overlap left inside it is a row that DIFFERS — and a row
        that matches perfectly is the strongest proof the two vocabularies
        meet, not the weakest. Without this the heuristic fired on a filing
        whose every mapped row agreed to the cent: 19 rows matching, zero
        differing, and the screen told the accountant the vocabulary was not
        mapped at all. The better the agreement, the more confidently it
        misreported.
        """
        self.ensure_one()
        computed_codes = {r["code"] for r in bad
                          if r["status"] == "only_computed"}
        matched = [r for r in bad if r["status"] == "differs"]
        if matched or agreeing or not computed_codes:
            return bad
        # No row matched and none differed: nothing here says the two
        # vocabularies have ever met.
        examples = ", ".join(sorted(computed_codes)[:6])
        return [{
            "code": _("(vocabulary not mapped)"),
            "filed": None,
            "computed": None,
            "diff": 0.0,
            "status": "unmapped",
            "detail": _(
                "%(n)d row(s) this filing does not carry under any name we "
                "recognise (%(examples)s%(more)s). Not %(n)d differences: the "
                "filed rows and the computed rows share no code at all, so "
                "the two vocabularies have not been mapped to each other. Map "
                "them and re-run — the real differences appear then.",
                n=len(computed_codes), examples=examples,
                more=", …" if len(computed_codes) > 6 else ""),
        }]

    @staticmethod
    def _cssk_row_is_empty(values):
        """Is there no money anywhere in this row's figures?

        A row-based form carries a TUPLE — a control statement row is
        (base, tax, rate, deduction, …) — so "empty" has to mean every figure
        in it is zero, not just the first. Asking ``abs()`` of the tuple is a
        TypeError, and testing only the leading figure would drop a row whose
        base is zero and whose daň is not.
        """
        if values is None:
            return True
        if isinstance(values, (int, float)):
            return abs(float(values)) < 0.005
        return all(abs(float(v)) < 0.005
                   for v in values if isinstance(v, (int, float)))

    def _cssk_drop_empty_rows(self, bad):
        """A row with no money on either side is not a finding.

        A form row we compute as zero that the filing simply did not carry is
        not a difference in either direction — the tax office cannot tell an
        unfiled row from a zero one. Reported, they crowd out the rows that
        are about money: on one real period, 32 of 38 one-sided rows were an
        empty row nobody filed, sitting around the two findings that mattered.

        NOT mirrored for a FILED zero, and the asymmetry is the point. A row
        the filing carries as 0.00 is a positive statement — the company
        reported nothing there — and disagreeing with it is a finding. A row
        we happen to leave empty says nothing at all.
        """
        return [r for r in bad
                if not (r["status"] == "only_computed"
                        and self._cssk_row_is_empty(r.get("computed")))]

    def _cssk_pair_classifications(self, bad):
        """Label the pairs where two engines agree on an amount and disagree
        about which row it belongs on.

        A supply the filing puts on one row and we put on another arrives as a
        row only the filing has and a row only we compute, offsetting each
        other exactly. That is ONE disagreement, and the question it raises is
        a different question — which box is right, not which number is. Left
        unpaired it reads as two independent errors and invites two answers.

        Measured on real data: a § 69 reverse charge filed on the goods pair
        and computed onto the services row, 59.00 on each side.
        """
        only_filed = [r for r in bad if r["status"] == "only_filed"]
        only_computed = [r for r in bad if r["status"] == "only_computed"]
        pairs = {}
        for left in only_filed:
            # Through the magnitude, not the raw value: a row-based form
            # compares tuples and ``abs()`` of one is a TypeError. The pairing
            # asks whether the same MONEY turned up on the other side, which
            # is the figure the difference column already stands on.
            amount = abs(self._cssk_compare_magnitude(left.get("filed")))
            if not amount:
                continue
            for right in only_computed:
                if right["code"] in pairs or right["code"] in pairs.values():
                    continue
                if abs(abs(self._cssk_compare_magnitude(
                        right.get("computed"))) - amount) < 0.005:
                    pairs[left["code"]] = right["code"]
                    pairs[right["code"]] = left["code"]
                    break
        return pairs

    #: Kinds that settle a row without anybody having to answer anything: it
    #: agrees, the gap is structural, or it was never a control to begin with.
    #: They are recorded so the comparison is complete, and they are kept out
    #: of the worklist by their state rather than by not existing.
    CSSK_SETTLED_KINDS = ("ok", "expected", "info")

    @staticmethod
    def _cssk_same_value(current, new):
        """Is a stored field value already what we are about to write?

        ``current`` comes off the record, so a Many2one reads as a recordset
        and a Monetary as a float that has been through the database's
        rounding. Compared naively, every row looks changed on every run.
        """
        if hasattr(current, "_name"):          # a recordset, e.g. company_id
            return current.id == new
        if isinstance(current, float) or isinstance(new, float):
            try:
                return abs(float(current or 0.0) - float(new or 0.0)) < 0.005
            except (TypeError, ValueError):
                return False
        return (current or False) == (new or False)

    # ------------------------------------------------------------------
    # the comparisons of this filing
    # ------------------------------------------------------------------
    # Only a COUNT is held. The link from a comparison back to its filing is a
    # loose ``(res_model, res_id)`` reference, so there is no inverse column
    # for a One2many to hang off; the action searches instead. Non-stored,
    # because the number changes whenever a comparison is run and a stored
    # copy would need invalidating from a model that does not know about this
    # one.
    cssk_comparison_count = fields.Integer(
        compute="_compute_cssk_comparison_count", string="Comparisons")

    def _compute_cssk_comparison_count(self):
        counts = {}
        if self.ids:
            # ``res_id`` is a plain Integer here, not a Many2one, so the
            # grouping key comes back as the integer itself rather than as a
            # recordset — which is why this does not unpack a record the way
            # the account.payment counterpart does.
            data = self.env["cssk.filing.comparison"]._read_group(
                [("res_model", "=", self._name), ("res_id", "in", self.ids)],
                ["res_id"], ["__count"])
            counts = {res_id: count for res_id, count in data}
        for rec in self:
            rec.cssk_comparison_count = counts.get(rec.id, 0)

    def action_cssk_open_comparisons(self):
        """The comparisons of this filing — all of them, one per basis."""
        self.ensure_one()
        comparisons = self.env["cssk.filing.comparison"].search(
            [("res_model", "=", self._name), ("res_id", "=", self.id)])
        action = {
            "type": "ir.actions.act_window",
            "name": _("Filed vs computed — %s", self.display_name),
            "res_model": "cssk.filing.comparison",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "target": "current",
        }
        # One comparison is the common case — a filing put only beside a
        # recomputation of itself — and landing on a one-row list to click it
        # is a step that says nothing.
        if len(comparisons) == 1:
            action.update(view_mode="form", res_id=comparisons.id)
        else:
            action.update(view_mode="list,form")
        return action

    def _cssk_comparison(self, basis, basis_label=False):
        """The comparison record for this filing on this basis, created once.

        Get-or-create rather than create-then-dedupe: the key is a UNIQUE
        constraint, and a comparison is re-run constantly — every recompute
        would otherwise race its own previous run. The descriptive fields are
        refreshed on every run because they can legitimately move (a filing
        gets renamed, a legacy source is corrected), but only when they have.
        """
        self.ensure_one()
        Comparison = self.env["cssk.filing.comparison"]
        vals = {
            "res_model": self._name, "res_id": self.id,
            "filing_name": self.display_name,
            "legacy_source": self.legacy_source or False,
            "company_id": self.company_id.id,
            "date_from": self.date_from, "date_to": self.date_to,
            "basis": basis, "basis_label": basis_label or False,
            "last_run_uid": self.env.uid,
            "last_run_date": fields.Datetime.now(),
        }
        domain = [("res_model", "=", self._name), ("res_id", "=", self.id),
                  ("basis", "=", basis)]
        record = Comparison.search(domain, limit=1)
        if not record:
            # SEARCH-THEN-CREATE IS A RACE, and this method is reached from a
            # button a user can double-click and from a cron that can overlap
            # a user. Both transactions miss, both create, the UNIQUE
            # constraint lets one through and the other dies with an
            # IntegrityError that aborts the whole comparison — losing the run
            # rather than merely duplicating a record.
            #
            # The savepoint is what makes the recovery possible at all: without
            # it the failed INSERT poisons the transaction and nothing further
            # can be executed on the cursor, so the re-search would fail too.
            try:
                with self.env.cr.savepoint():
                    return Comparison.create(vals)
            except IntegrityError:
                # The other transaction won and has committed its row by the
                # time we look again — so this is a plain re-read, not a retry
                # loop, and it falls through to the update path below.
                self.env.cr.flush()
                record = Comparison.search(domain, limit=1)
                if not record:
                    raise
        changed = {k: v for k, v in vals.items()
                   if not self._cssk_same_value(record[k], v)}
        if changed:
            record.write(changed)
        return record

    def _cssk_upsert_comparison_rows(self, rows, basis, basis_label=False):
        """Persist one comparison's rows, every answer on them preserved.

        ``rows`` are ``{code, label, filed, computed, diff, kind, detail}`` —
        deliberately a plain shape, because the callers are not all the same
        comparison. Keyed on (filing, basis, row): a re-run refreshes the
        figures and leaves the state and the note exactly as somebody left
        them, because carrying an accountant's answer across a recompute is
        the whole point. A row that stops appearing is marked ``stale``,
        never deleted.

        Returns ``{code: record}`` so a caller can link rows to each other.
        """
        self.ensure_one()
        Discrepancy = self.env["cssk.filing.discrepancy"]
        comparison = self._cssk_comparison(basis, basis_label)
        existing = {d.code: d for d in Discrepancy.search([
            ("comparison_id", "=", comparison.id)])}
        common = {
            "comparison_id": comparison.id,
            "res_model": self._name, "res_id": self.id,
            "filing_name": self.display_name,
            "legacy_source": self.legacy_source or False,
            "company_id": self.company_id.id,
            "date_from": self.date_from, "date_to": self.date_to,
            "basis": basis, "basis_label": basis_label or False,
        }
        seen, written = set(), {}
        for row in rows:
            code = row["code"]
            seen.add(code)
            settled = row["kind"] in self.CSSK_SETTLED_KINDS
            vals = dict(common, code=code, kind=row["kind"],
                        row_label=row.get("label") or False,
                        filed=row.get("filed") or 0.0,
                        computed=row.get("computed") or 0.0,
                        difference=row.get("diff") or 0.0,
                        detail=row.get("detail") or False,
                        stale=False)
            record = existing.get(code)
            if record:
                # The state is the machine's only while nobody has engaged
                # with it: ``open`` and ``agrees`` both mean "nobody has said
                # anything yet", so they follow the figures. Anything else is
                # somebody's answer and is left alone — including on a row
                # that now agrees, where a conversation still has to be
                # closed by the person who opened it.
                if record.state in ("open", "agrees"):
                    vals["state"] = "agrees" if settled else "open"
                # Only write what moved. A comparison is re-run on every
                # change and most rows never move, so writing them anyway
                # churns ``write_date`` on thousands of records, fires the
                # tracking machinery, and makes "when did this last change"
                # unanswerable — on a real agenda this loop is ~40 rows on
                # each of ~220 filings.
                changed = {k: v for k, v in vals.items()
                           if not self._cssk_same_value(record[k], v)}
                if changed:
                    record.write(changed)
            else:
                record = Discrepancy.create(
                    dict(vals, state="agrees" if settled else "open"))
            written[code] = record
        for record in [d for code, d in existing.items() if code not in seen]:
            record.stale = True
        return written

    def _cssk_record_discrepancies(self, result):
        """Persist the filed-vs-recomputed comparison, agreeing rows included.

        The agreeing rows are not decoration. A migration is judged by how
        much of it landed, and a screen carrying only the failures cannot
        answer that: on the agenda this was built for, 583 of 608 rows agree
        and there was no way to see it. They are written in state ``agrees``
        so the worklist stays a worklist.
        """
        self.ensure_one()
        bad = [r for r in result["rows"]
               if r["status"] not in ("ok", "not_stated")]
        agreeing = [r for r in result["rows"] if r["status"] == "ok"]
        # Rows the source cannot state are recorded, never counted: they are
        # neither agreement nor error, and burying three of them a month in
        # the worklist is how a real finding goes unread.
        unstated = [
            dict(row, kind="info", detail=_(
                "The source system's own filing has no figure for this row, "
                "so there is nothing to compare. What we compute is shown for "
                "information."))
            for row in result["rows"] if row["status"] == "not_stated"
        ]
        # Order matters. The collapse decides whether the two VOCABULARIES
        # meet and must see every row to do it; the zero-drop then removes
        # non-findings from what is reported individually. Dropping first
        # would let a filing whose every computed counterpart is empty look
        # like a mapped vocabulary.
        collapsed = self._cssk_collapse_unmapped(bad, len(agreeing))
        if collapsed is bad:
            bad = self._cssk_drop_empty_rows(bad)
        else:
            # Collapsing means nothing met, so there is nothing to agree —
            # the count is what stopped it from collapsing in the first place.
            bad = collapsed
        pairs = self._cssk_pair_classifications(bad)
        rows = [
            dict(row, kind=("classification" if row["code"] in pairs
                            else ("amount" if row["status"] == "differs"
                                  else row["status"])))
            for row in bad
        ]
        rows += [dict(row, kind="ok") for row in agreeing]
        rows += unstated
        # ⚠️ A ROW-BASED form compares TUPLES, not floats — a control statement
        # row is (base, tax, …) and an EC sales row is (partner, hodnota). The
        # monetary fields take one figure, so each side goes through the same
        # reduction the difference column already uses. Handing the tuple
        # straight to ``write`` is an ORM error on the KV and the súhrnný
        # výkaz, which are exactly the two forms that override
        # ``_cssk_comparable_rows``.
        for row in rows:
            row["filed"] = self._cssk_compare_magnitude(row.get("filed"))
            row["computed"] = self._cssk_compare_magnitude(row.get("computed"))
        # No basis_label. It used to carry _("the same filing, recomputed from
        # the ledger"), which restates the `basis` selection the screen already
        # shows translated — and being STORED it was written in the runner's
        # language, so it was the other half of the English-labels problem. The
        # labels that remain on other bases name specific records ("DPH
        # priznanie FA/2017/06", "účtovníctvo — účet 343") and are Slovak in
        # source, so they carry information the selection cannot.
        written = self._cssk_upsert_comparison_rows(rows, "recomputed")
        # A row that was half of a classification pair and is not any more
        # must lose the link, or the form offers a counterpart that no longer
        # says anything about it.
        for code, record in written.items():
            other = pairs.get(code)
            target = written[other].id if other in written else False
            if record.counterpart_id.id != target:
                record.counterpart_id = target
        return {"recorded": len(bad), "agreed": len(agreeing),
                "not_stated": len(unstated)}

    def action_cssk_compare_to_computed(self):
        """Compare, record every row, and open the comparison.

        No chatter. The comparison IS the rows — queryable, answerable, and
        carrying what the accountant said — and posting a copy of them on
        every re-run buries the record it is supposedly documenting.
        """
        self.ensure_one()
        result = self._cssk_compare_to_computed()
        if not result["comparable"]:
            raise UserError(result["reason"])
        self._cssk_record_discrepancies(result)
        return self._cssk_comparison_action(
            "recomputed", _("Filed vs computed — %s", self.display_name))

    def _cssk_comparison_action(self, basis, name):
        """The comparison screen for this filing, on one basis.

        No default filter: opened from the button, the point is to see the
        whole comparison, agreeing rows and all. The menu action keeps its
        worklist filter, which is a different question.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "cssk.filing.discrepancy",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id),
                       ("basis", "=", basis)],
            "context": {"search_default_live": 1},
            "target": "current",
        }

    # ------------------------------------------------------------------
    # period selection
    # ------------------------------------------------------------------
    #: Move types whose period is governed by the tax point. Everything else
    #: — vendor bills, entries, bank and cash — is governed by the accounting
    #: date; see ``_cssk_period_move_ids``.
    CSSK_TAX_POINT_MOVE_TYPES = ("out_invoice", "out_refund")

    def _cssk_period_move_ids(self, company, date_from, date_to):
        """Moves belonging to a VAT-derived statutory period.

        The basis is **not the same on both sides of the return**, and getting
        that wrong moves real money between periods:

        * **Output** — uskutočnené / uskutečněná plnění — is declared for the
          period of the **tax point** (DUZP, deň dodania). The obligation
          arises with the supply, not with the bookkeeping.
        * **Input** — the deduction — is claimed for the period in which the
          right is *exercised*, which CZ § 73 and the SK equivalent allow to be
          later than the supply. That is ``cssk_vat_deduction_date`` where the
          document records one, and otherwise the accounting date, which is the
          right proxy for the ordinary case of a bill booked in the period it is
          claimed.

        Using the tax point on both sides looks tidier and is wrong. Measured
        against one company's filed return, 84,730 of deductible base sat on
        documents supplied before the period and claimed inside it — reporting
        those by supply date understates the deduction by exactly that much.

        Documents with no tax point at all (entries, bank, cash) follow the
        accounting date, which is the only date they have.

        ``taxable_supply_date`` is core in Odoo 19 but came from the country
        modules in 18.0, so its presence is checked rather than assumed.

        The period test is resolved on ``account.move`` and returned as ids
        deliberately: a ``= False`` leaf reached through a ``move_id.`` path
        does not match the rows with no tax point at all, which silently drops
        every entry, bank and cash document out of the statement.

        With the context key ``cssk_period_ignore_declared_date`` the rule is
        evaluated as if no document recorded a ``cssk_vat_deduction_date``.
        That is a hook for a module that knows a declared period does not
        apply to some documents (``l10n_cz_vat_status``: a non-payer has no
        deduction to defer); it takes the answer for those documents from
        this pass, so the fallback rule stays written down once, here.
        """
        Move = self.env["account.move"]
        honour_declared = (
            "cssk_vat_deduction_date" in Move._fields
            and not self.env.context.get("cssk_period_ignore_declared_date"))
        base = [("company_id", "=", company.id), ("state", "=", "posted")]
        by_date = [("date", ">=", date_from), ("date", "<=", date_to)]
        if "taxable_supply_date" not in Move._fields:
            return Move.search(base + by_date).ids

        tax_point_types = list(self.CSSK_TAX_POINT_MOVE_TYPES)
        supply_leaves = [
            "|",
            "&", "&",
            ("taxable_supply_date", "!=", False),
            ("taxable_supply_date", ">=", date_from),
            ("taxable_supply_date", "<=", date_to),
            "&", "&",
            ("taxable_supply_date", "=", False),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if honour_declared:
            # An EXPLICITLY RECORDED declaration period wins over the tax point
            # on the output side too, and only where one is recorded — a
            # document raised in Odoo leaves the field empty and follows the
            # tax point exactly as before, so this changes nothing for ordinary
            # work.
            #
            # It matters for two real cases that the tax point gets wrong, both
            # of which the taxpayer handles the same way:
            #
            # * a § 42 correction is declared for the period in which the
            #   corrective document reached the customer, not for its own
            #   taxable-supply date;
            # * a document entered late is declared in the period it was
            #   entered rather than through a supplementary return.
            #
            # Measured over seven years of one imported agenda, recomputing all
            # 59 filed control statements both ways — output by tax point
            # against output by declared period:
            #
            #     A4  periods exact  40 → 46   gross difference 2 900 104 → 290 059
            #     A5  periods exact  30 → 55   gross difference   186 129 →  26 542
            #     all seven exact    13 → 20
            #
            # and A1, A2, B1, B2, B3 identical to the row. Ten times closer on
            # the largest section, nothing worse anywhere.
            supply_leaves = [
                "|", "|",
                "&", "&",
                ("cssk_vat_deduction_date", "!=", False),
                ("cssk_vat_deduction_date", ">=", date_from),
                ("cssk_vat_deduction_date", "<=", date_to),
                "&", "&", "&",
                ("cssk_vat_deduction_date", "=", False),
                ("taxable_supply_date", "!=", False),
                ("taxable_supply_date", ">=", date_from),
                ("taxable_supply_date", "<=", date_to),
                "&", "&", "&",
                ("cssk_vat_deduction_date", "=", False),
                ("taxable_supply_date", "=", False),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
        supply_side = Move.search(
            base + [("move_type", "in", tax_point_types)] + supply_leaves
        )
        # The claim side prefers an explicit deduction date where the document
        # carries one: the accounting date is only a proxy for "the period the
        # deduction is exercised", and the two part company exactly when a bill
        # is booked in one period and claimed in the next.
        # The claim side, in two populations rather than one, because the
        # tax-point preference below is about ENTRIES and used to capture bills
        # as well.
        #
        # An entry that carries a tax point is telling you something: a § 92a
        # reverse charge booked on 22 July and declared on 31 December belongs
        # to December, and taking its accounting date put it five months early
        # and counted it twice. An INVOICE's tax point says nothing about when
        # the deduction is claimed — CZ § 73 lets that be later, and the
        # ordinary case is a bill supplied in May, booked in June and deducted
        # in June. Preferring its tax point reported it in May.
        #
        # That is what the module's own docstring above has always said —
        # "``cssk_vat_deduction_date`` where the document records one, and
        # otherwise the accounting date" — and what three tests asserted while
        # the code did something else.
        invoice_like = ["in_invoice", "in_refund", "in_receipt", "out_receipt"]
        claim_base = base + [("move_type", "not in", tax_point_types)]
        if "cssk_vat_deduction_date" in Move._fields:
            undeclared = (
                [("cssk_vat_deduction_date", "=", False)] if honour_declared
                else [])
            declared = [
                "&", "&",
                ("cssk_vat_deduction_date", "!=", False),
                ("cssk_vat_deduction_date", ">=", date_from),
                ("cssk_vat_deduction_date", "<=", date_to),
            ]
            claim_side = (Move.search(claim_base + declared)
                          if honour_declared else Move.browse())
            # No declaration: an entry falls back to its tax point, everything
            # else to its accounting date.
            claim_side |= Move.search(
                claim_base
                + undeclared
                + [("move_type", "not in", invoice_like)]
                + [
                    "|",
                    "&", "&",
                    ("taxable_supply_date", "!=", False),
                    ("taxable_supply_date", ">=", date_from),
                    ("taxable_supply_date", "<=", date_to),
                    "&", "&",
                    ("taxable_supply_date", "=", False),
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                ]
            )
            claim_side |= Move.search(
                claim_base
                + undeclared
                + [("move_type", "in", invoice_like)]
                + [("date", ">=", date_from), ("date", "<=", date_to)]
            )
        else:
            claim_side = Move.search(
                claim_base + [("date", ">=", date_from), ("date", "<=", date_to)]
            )

        return (supply_side | claim_side).ids

    def _ensure_not_submitted(self):
        """Concrete ``action_export_xml`` / recompute calls this to stay safe."""
        for rec in self:
            if rec.state == "submitted":
                raise UserError(_(
                    "This filing was marked submitted on %s and is locked. "
                    "Reset it to draft if you really need to re-export or "
                    "recompute (the filed copy is preserved).",
                    rec.submitted_date))

    # ------------------------------------------------------------------
    # Master-data preflight (fail early, instead of a cryptic XSD error)
    # ------------------------------------------------------------------
    def _cssk_preflight_export(self):
        """Check the master data the official XML template emits BEFORE
        rendering, so the user gets a named field instead of a cryptic XSD
        validation error. Called at the start of each statement's
        ``action_export_xml``.

        Base implementation: every CZ/SK statutory template emits the
        company's VAT number (IČ DPH / DIČ z DPH) as the filer identification.
        Statement bases / country modules extend this with form-specific
        checks (per-row partner VAT, supply dates, …).
        """
        for rec in self:
            company = getattr(rec, "company_id", None)
            if company is not None and not company.vat:
                raise UserError(_(
                    "Company '%(company)s' has no VAT number set, but the "
                    "exported XML must carry it as the filer identification. "
                    "Set the 'Tax ID' (VAT) field on the company (Settings → "
                    "Users & Companies → Companies → %(company)s) and export "
                    "again.", company=company.display_name))
        return True

    # ------------------------------------------------------------------
    # Export pipeline (consolidated — see the module docstring)
    # ------------------------------------------------------------------
    def action_export_xml(self):
        self.ensure_one()
        self._cssk_check_not_legacy(_("exported"))
        self._ensure_not_submitted()
        if self.state == "draft":
            raise UserError(self._cssk_export_draft_error())
        self._cssk_preflight_export()
        # Content checks run BEFORE rendering (fail fast on a named rule,
        # never masked by a template/XSD problem).
        self._cssk_check_kontroly()
        xml_bytes = self._render_xml()
        self._validate_against_schema(xml_bytes)
        self._attach_xml(xml_bytes)
        self.state = "exported"
        return True

    def _cssk_export_draft_error(self):
        """State-gate wording hook (a draft record has nothing to export)."""
        return _("Compute the statement before exporting.")

    def _cssk_check_kontroly(self):
        """Content-check stage hook, run BEFORE rendering.

        Default: no-op. Statement bases / country modules override this —
        typically with ``self._cssk_enforce_kontroly()`` plus any extra
        gates (e.g. the EC sales list's VIES check).
        """
        self.ensure_one()
        return True

    def _cssk_enforce_kontroly(self):
        """Run ``check_kontroly()`` and enforce its verdict: severity
        ``error`` blocks the export, warnings are logged. Returns the full
        violation list."""
        self.ensure_one()
        violations = self.check_kontroly()
        errors = [v for v in violations
                  if v.get("severity", "error") == "error"]
        if errors:
            raise UserError(_(
                "The %(form)s failed kontrolné pravidlá:\n%(details)s",
                form=self.env._(self._cssk_form_label),
                details="\n".join("  • %s: %s" % (v["desc"], v["detail"])
                                  for v in errors)))
        if violations:
            _logger.warning(
                "%s kontrolné pravidlá warnings:\n%s", self.display_name,
                "\n".join("  • %s: %s" % (v["desc"], v["detail"])
                          for v in violations))
        return violations

    def _cssk_render_context(self):
        """QWeb rendering context; bases add their form-specific variables
        (line values, sections, comparison periods, …)."""
        self.ensure_one()
        return {"statement": self, "company": self.company_id}

    def _render_xml(self):
        self.ensure_one()
        content = self.env["ir.qweb"]._render(
            self.version_id.xml_template_ref_id.id,
            self._cssk_render_context())
        # ir.qweb._render returns Markup; emit a UTF-8 XML declaration + body.
        body = str(content).strip()
        return ('<?xml version="1.0" encoding="UTF-8"?>\n' + body).encode(
            "utf-8")

    def _cssk_schema_optional(self):
        """May this form export without validating against an XSD?

        False everywhere unless the form's own version record says otherwise,
        so the answer is DATA a maintainer wrote down per vintage, not a
        property some model quietly inherits. Feature-detected rather than
        assumed: only the financial statements carry the flag today, because
        only they have a form with no published schema.
        """
        self.ensure_one()
        version = self.version_id
        return bool(
            "xml_schema_optional" in version._fields
            and version.xml_schema_optional)

    def _validate_against_schema(self, xml_bytes):
        self.ensure_one()
        version = self.version_id
        root = etree.fromstring(xml_bytes)
        if version.xml_root_element and etree.QName(root).localname != (
            version.xml_root_element
        ):
            raise UserError(
                _("Rendered XML root <%(got)s> does not match expected "
                  "<%(exp)s>.")
                % {"got": etree.QName(root).localname,
                   "exp": version.xml_root_element}
            )
        if not version.xml_schema_data:
            # ⚠️ A version with no schema binary used to return here silently:
            # the document exported, the root-element check passed, the state
            # became `exported` and the XML was attached, with nothing anywhere
            # saying it had never been validated.
            #
            # That is the worst available behaviour for this particular check.
            # The whole reason a form VERSION carries its own schema is that an
            # envelope validated against the wrong vzor — or against nothing —
            # is rejected at submission rather than here, by which point the
            # filing is late. A skipped check that looks like a passed one is
            # exactly the failure the versioning exists to prevent.
            #
            # Found when a KV DPH 2023 export appeared to validate and had not:
            # the root element was right, the schema absent, and the only
            # evidence of validation was a line in the operator's own script.
            #
            # ⚠️ But it must not refuse a form that HAS no schema to load.
            # Rozvaha, VZZ and the two CZ přehledy are filed as attachments
            # inside the DPPO envelope and no XSD is published for any of
            # them, so the raise made every Czech financial-statement export
            # impossible — the check aimed at a missing file and hit a form
            # where absence is the published state of the world. That is the
            # version's business to declare, because the same form family
            # differs by country: Úč POD ships uzpod-2014.xsd.
            if self._cssk_schema_optional():
                _logger.info(
                    "%s %s exported without schema validation: version %s "
                    "declares that no official XSD exists for this form",
                    self._name, self.id, version.display_name)
                return
            raise UserError(_(
                "%(form)s cannot be exported: the form version %(version)s "
                "carries no XML schema, so the document cannot be validated. "
                "Load the official XSD onto the version before exporting — "
                "an unvalidated file is rejected on submission, not here.",
                form=self.env._(self._cssk_form_label), version=version.display_name,
            ))
        schema = etree.XMLSchema(
            etree.fromstring(base64.b64decode(version.xml_schema_data))
        )
        try:
            schema.assertValid(root)
        except etree.DocumentInvalid as exc:
            raise UserError(_(
                "The %(form)s XML failed schema validation:\n%(err)s",
                form=self.env._(self._cssk_form_label), err=exc)) from exc

    def _attach_xml(self, xml_bytes):
        self.ensure_one()
        self.xml_attachment_id = self.env["ir.attachment"].create(
            {
                "name": "%s.xml" % (self.name or self._cssk_xml_name_fallback),
                "datas": base64.b64encode(xml_bytes),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/xml",
            }
        )

    # ------------------------------------------------------------------
    # Shared evaluator plumbing: batched account-balance maps
    # ------------------------------------------------------------------
    # The FS / income-tax evaluators (and the per-line reconciliation
    # health checks) all reduce to "sum posted move-line balances by
    # account-code prefix". Doing that as one search per prefix per line is
    # O(lines × prefixes) queries; instead fetch ONE {account_code: balance}
    # map per period window with a single grouped query and do the prefix
    # matching in Python.

    def _cssk_balance_groups(self, domain, company=None, as_of=False):
        """``{reported_code: [summed balance, [account ids]]}`` of the
        ``account.move.line`` records matching ``domain`` — one
        ``_read_group`` (grouped by account). ``company`` resolves the
        company-dependent account code and its statement account mapping
        (``cssk.statement.account.map``); ``as_of`` says the window is a
        cumulative balance, the only one a debit- or credit-only mapping
        applies to."""
        groups = self.env["account.move.line"]._read_group(
            domain, groupby=["account_id"], aggregates=["balance:sum"])
        Map = self.env["cssk.statement.account.map"]
        mapping = Map._cssk_map_for(company) if company else {}
        result = {}
        for account, balance in groups:
            if company:
                account = account.with_company(company)
            balance = balance or 0.0
            code = Map._cssk_reported_code(
                mapping, account.id, account.code or "", balance, as_of)
            entry = result.setdefault(code, [0.0, []])
            entry[0] += balance
            entry[1].append(account.id)
        return result

    def _cssk_balances_by_account_code(self, domain, company=None,
                                       as_of=False):
        """``{account_code: summed balance}`` — see ``_cssk_balance_groups``;
        the code is the one the account is REPORTED under."""
        return {
            code: entry[0]
            for code, entry in self._cssk_balance_groups(
                domain, company=company, as_of=as_of).items()
        }

    def _cssk_account_balance_domain(self, date_from, date_to):
        """The ``account.move.line`` domain behind
        ``_cssk_account_balance_map`` — shared with the drill-down, so the
        journal items a row opens are the ones its figure was summed from."""
        self.ensure_one()
        domain = [
            ("parent_state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            ("date", "<=", date_to),
        ]
        if date_from:
            domain.append(("date", ">=", date_from))
        closing = self.company_id.l10n_cssk_closing_journal_ids
        if closing:
            domain.append(("journal_id", "not in", closing.ids))
        return domain

    def _cssk_account_balance_groups(self, date_from, date_to):
        """``_cssk_account_balance_map`` with the account ids kept."""
        self.ensure_one()
        if not date_to:
            return {}
        return self._cssk_balance_groups(
            self._cssk_account_balance_domain(date_from, date_to),
            company=self.company_id, as_of=not date_from)

    def _cssk_account_balance_map(self, date_from, date_to):
        """The statement's posted balances per account code for a period
        window: ``date_from`` set → movement ``[date_from, date_to]``;
        ``None`` → cumulative balance as of ``date_to``.

        Year-end closing / reopening journals configured on the company
        (``l10n_cssk_closing_journal_ids``) are excluded — see the field's
        comment for why both halves go and why this is keyed on journals
        rather than on accounts 701/702/710."""
        self.ensure_one()
        if not date_to:
            return {}
        return self._cssk_balances_by_account_code(
            self._cssk_account_balance_domain(date_from, date_to),
            company=self.company_id, as_of=not date_from)

    # ------------------------------------------------------------------
    # Shared evaluator plumbing: ONE account-code matcher
    # ------------------------------------------------------------------
    # Every statutory statement reduces to "sum posted balances by account-code
    # prefix", and each one used to carry its own copy of that loop: the FS
    # statement, the income-tax return and the SK Úč POD XML builder. The copies
    # had drifted — the XML builder grew a synthetic-absorb rule and conditional
    # terms the others never got — so the figures an accountant previewed did
    # not have to equal the figures that were filed. One implementation, three
    # callers, each keeping its own conventions through arguments.
    #
    # Two conventions genuinely differ and must NOT be normalised away:
    #   * sign — the FS reads a formula's bare prefix as +1 and '-' as −1; the
    #     income-tax return is inverted (bare = −1, '-' = +1, so that the net
    #     comes out as a positive profit). Hence ``default_sign``.
    #   * absorb — passing ``claimed`` turns on the rule where a synthetic-main
    #     token NNN000 picks up every analytic of synthetic NNN that no other
    #     row claims. Passing None keeps plain prefix matching. It is opt-in
    #     because CZ row definitions already use 6-digit tokens (343000 next to
    #     343001/343112) where absorbing would silently change filed figures.

    @staticmethod
    def _cssk_split_token(token, tag_codes):
        """``(sign_is_negated, prefix, include, exclude)`` for one raw token.

        A token may carry account-tag filters for the SK VZS related-party
        split: ``665&IX_1`` keeps only accounts tagged IX_1, ``665!IX_1!IX_2``
        excludes them."""
        # Whether tag operators mean anything is the CALLER's choice, and the
        # test is ``is not None``, not truthiness. Three-way constraint:
        #
        #  * the SK builder passes a dict (possibly with every value an empty
        #    set) and needs ``665!IX_1!IX_2`` parsed even then — with nothing
        #    tagged the exclusion is empty and the whole of 665 belongs on that
        #    row. That IS the "ostatné" leaf, and it is the no-setup default.
        #    Gate on truthiness and an empty-but-present dict leaves the token
        #    literal, matching no account code, silently reporting zero.
        #  * the FS statement and the income-tax return pass nothing. Their
        #    original evaluators had no tag support at all and treated such a
        #    token as a literal prefix. Parsing it for them would change filed
        #    figures on any formula that happened to contain & or !.
        tags_enabled = tag_codes is not None
        tag_codes = tag_codes or {}
        token = (token or "").strip()
        negated = token.startswith("-")
        token = token.lstrip("-").strip()
        include, exclude = None, set()
        if tags_enabled and ("&" in token or "!" in token):
            match = re.match(r"([0-9]+)(.*)", token)
            if match:
                token = match.group(1)
                for op, name in re.findall(
                        r"([&!])([A-Za-z0-9_]+)", match.group(2)):
                    if op == "&":
                        include = (include or set()) | tag_codes.get(name, set())
                    else:
                        exclude |= tag_codes.get(name, set())
        return negated, token, include, exclude

    @staticmethod
    def _cssk_code_matches(code, prefix, claimed):
        """Does ``code`` fall under ``prefix``?

        With ``claimed`` supplied, a 6-character token ending in 000 is a
        synthetic-main token: it takes every analytic of its 3-digit synthetic
        that is not explicitly routed to some other row (so 022000 picks up
        022001 and 022002, and also a non-numeric analytic like 131ved, but
        never 022150 if some row names 022150 outright)."""
        if not code:
            return False
        if claimed is not None and len(prefix) == 6 and prefix.endswith("000"):
            return code[:3] == prefix[:3] and code[:6] not in claimed
        # Group residual: "02X" on a statutory form means "any OTHER account of
        # group 02 that no row names" — one level up from the synthetic
        # residual above. The Slovak Súvaha writes its catch-all rows that way
        # ("029, 02X, 032" on r017), and reading 02X as the bare prefix 02
        # double-counts every account the named rows already took: a balance on
        # 022 lands on its own row AND on the catch-all, and their common
        # parent reports it twice.
        if claimed is not None and len(prefix) == 3 and prefix.endswith("X"):
            return code[:2] == prefix[:2] and code[:3] not in claimed
        return code.startswith(prefix)

    @api.model
    def _cssk_eval_formula(self, formula, balances, conds=None,
                           default_sign=1.0, claimed=None, tag_codes=None,
                           two_sided=None, contributors=None):
        """Signed sum of ``{account_code: balance}`` matching ``formula``.

        ``formula`` is a comma-separated list of account-code prefixes; a
        leading '-' negates that token's contribution. An account matched by
        two tokens contributes once PER TOKEN — the historical semantics of
        all three evaluators, relied on by existing row definitions.

        ``conds`` are ``[low, high, mode, sign]`` terms adding ``sign × net``
        over accounts with ``low <= code < high`` — the split that routes a
        balance to one row or the other according to its sign (a tax account to
        receivable or payable; a bank account to asset or overdraft).

        Modes:

        ``pos_each`` / ``neg_each``
            Gate **per account**: sum only the accounts whose OWN balance
            carries the required sign. This is the correct behaviour whenever
            accounts in the range can offset each other, which is the normal
            case — a company with 50k on one bank account and −1.8M on another
            holds both an asset and a debt, not a single net debt.
        ``pos`` / ``neg``
            Gate on the AGGREGATE net of the whole range, all-or-nothing. Kept
            for compatibility with definitions written against the old
            behaviour; prefer the ``_each`` forms for anything new. Note the
            failure mode: one offsetting balance flips the entire range to the
            other row and the opposite-signed part vanishes from the statement
            without trace.
        ``sum``
            Unconditional.

        ``two_sided`` is a set of prefixes the form names on BOTH sides of the
        sheet — a bank account is an asset when it is in funds and a
        krátkodobá finančná výpomoc when it is overdrawn; 341-347, 336, 373,
        398 and 481 are a pohľadávka or a záväzok by the same test. For those
        prefixes the token's own sign says which side it is claiming, so each
        account is gated on its OWN balance: a positive token takes only debit
        balances, a negative token only credit ones. Without the gate the same
        balance lands on both sides at once and the sheet foots to double the
        truth. Left ``None`` the gate is off and every prefix sums as before.

        ``contributors``, when a set is passed, receives every code that added
        to the total — what the row's drill-down must open, decided by this
        matcher and not by a second reading of the formula."""
        if two_sided and default_sign < 0:
            # The gate reads the token's own '-' so that it says which SIDE of
            # the sheet the row is claiming, independent of a caller's global
            # sign convention. Under a negative default_sign the two readings
            # come apart, and the wrong half of every two-sided account would
            # be taken — quietly, with a plausible number. No caller does this
            # today; refuse rather than let one start.
            raise ValueError(
                "two_sided gating requires a positive default_sign")
        total = 0.0
        for raw in (formula or "").split(","):
            negated, prefix, include, exclude = self._cssk_split_token(
                raw, tag_codes)
            if not prefix:
                continue
            sign = -default_sign if negated else default_sign
            for code, balance in balances.items():
                if include is not None and code not in include:
                    continue
                if code in exclude:
                    continue
                if not self._cssk_code_matches(code, prefix, claimed):
                    continue
                if two_sided and prefix.upper() in two_sided:
                    # The token's sign is a claim about which side of the
                    # sheet this account belongs on; honour it per account.
                    # (Read off ``negated``, not ``sign``, so the gate stays
                    # right for a caller that passes default_sign=-1.)
                    if negated != (balance < 0):
                        continue
                total += sign * balance
                if contributors is not None:
                    contributors.add(code)
        for low, high, mode, csign in (conds or []):
            in_range = [(code, balance) for code, balance in balances.items()
                        if code and low <= code < high]
            if mode == "pos_each":
                taken = [(c, b) for c, b in in_range if b > 0]
            elif mode == "neg_each":
                taken = [(c, b) for c, b in in_range if b < 0]
            else:
                net = sum(b for _c, b in in_range)
                taken = in_range if (
                    mode == "sum" or (mode == "pos" and net > 0)
                    or (mode == "neg" and net < 0)) else []
            total += csign * sum(b for _c, b in taken)
            if contributors is not None:
                contributors.update(c for c, _b in taken)
        return total

    @api.model
    def _cssk_unmapped_codes(self, balances, cells, claimed=None,
                             tag_codes=None):
        """``[(code, balance)]`` for accounts that match NO row, worst first.

        The failure this exists to catch is silent: an account whose code no
        row's formula covers simply contributes to nothing, and the statement
        still foots, still balances against itself, and still looks plausible.
        A trial balance that comes to zero cannot detect it either — a balanced
        ledger says nothing about whether every account reached a row. It shows
        up only when someone ties the statement back to an outside source.

        ``cells`` is an iterable of ``(formula, conds)`` covering every row of
        every statement the codes are expected to land in."""
        cells = [
            (f or "", c or [])
            for f, c in cells
            if (f or "").strip() or c
        ]
        unmapped = []
        for code, balance in balances.items():
            if not code:
                continue
            hit = False
            for formula, conds in cells:
                for raw in formula.split(","):
                    _, prefix, _, _ = self._cssk_split_token(raw, tag_codes)
                    if prefix and self._cssk_code_matches(code, prefix, claimed):
                        hit = True
                        break
                if hit:
                    break
                if any(low <= code < high for low, high, _m, _s in conds):
                    hit = True
                    break
            if not hit:
                unmapped.append((code, balance))
        return sorted(unmapped, key=lambda cb: (-abs(cb[1]), cb[0]))

    def action_submit(self):
        self._cssk_check_not_legacy(_("submitted"))
        for rec in self:
            if rec.state != "exported":
                raise UserError(_(
                    "Export the XML before marking the filing submitted."))
            if not rec.xml_attachment_id:
                raise UserError(_("There is no exported XML to submit."))
            rec.submitted_attachment_id = rec.xml_attachment_id
            # Durable filed-copy trail: 'submitted_attachment_id' is only the
            # LATEST filed copy — after reset → recompute → resubmit it points
            # to the new XML, so every submitted attachment is also accumulated
            # in filed_history_ids (the originally-filed XML stays reachable).
            rec.filed_history_ids = [Command.link(rec.xml_attachment_id.id)]
            rec.submitted_date = fields.Datetime.now()
            rec.state = "submitted"
            # Markup on the TEMPLATE, interpolation through ``%`` so the
            # attachment name is escaped. ``Markup(_( ... , args))`` would
            # render whatever the filename contains.
            rec.message_post(body=Markup(
                _("Marked <b>submitted</b> on %(date)s. Filed copy: %(name)s")
            ) % {
                "date": fields.Datetime.to_string(rec.submitted_date),
                "name": rec.submitted_attachment_id.name or "—",
            })
        return True

    def unlink(self):
        for rec in self:
            if rec.state == "submitted":
                raise UserError(_(
                    "%(name)s is marked submitted and cannot be deleted. "
                    "Reset it to draft first if you really need to remove it "
                    "(the filed copy is preserved).",
                    name=rec.display_name))
        return super().unlink()

    def action_reset_to_draft(self):
        # Unlocking a statutory filing is a manager-level decision: it reopens
        # a record whose filed XML is the legal baseline of the period.
        if not self.env.su and not self.env.user.has_group(
                "account.group_account_manager"):
            raise UserError(_(
                "Only Accounting administrators (group 'Accounting / "
                "Administrator') may reset a statutory filing to draft."))
        for rec in self:
            if rec.state == "draft":
                continue
            was = rec.state
            rec.state = "draft"
            rec.message_post(body=_(
                "Reset to draft (from %s). Filed copy preserved: %s",
                was, rec.submitted_attachment_id.name or "—"))
        return True

    # ------------------------------------------------------------------
    # Amendment (dodatočné / opravné priznanie)
    # ------------------------------------------------------------------
    # A dodatočné priznanie amends an already-filed one and needs the original
    # as the "posledná známa daň" baseline. ``action_create_amendment`` copies
    # the original into a fresh draft, links it (``original_return_id``) and
    # keeps the original's manual overrides as the starting point; it does NOT
    # carry the filed XML / submission stamps (those are copy=False). The user
    # then picks the Dodatočný / Opravný submission type, adjusts the accounting
    # and recomputes — form-specific difference rows (e.g. DPH r36) fill from the
    # link. The concrete model must define ``original_return_id`` (M2o to self).

    def action_create_amendment(self):
        self.ensure_one()
        if "original_return_id" not in self._fields:
            raise UserError(_("This filing does not support amendments."))
        amendment = self.copy({
            "original_return_id": self.id,
            "state": "draft",
            "xml_attachment_id": False,
        })
        # "deň zistenia" defaults to today (when the amendment is raised); the
        # accountant can correct it. Only forms that have the field (DPH) carry it.
        if "discovery_date" in amendment._fields and not amendment.discovery_date:
            amendment.discovery_date = fields.Date.context_today(amendment)
        amendment.message_post(body=_(
            "Dodatočné / opravné podanie k pôvodnému: %s.", self.display_name))
        self.message_post(body=_(
            "Vytvorené dodatočné / opravné podanie: %s.", amendment.display_name))
        return {
            "type": "ir.actions.act_window",
            "name": _("Dodatočné / opravné podanie"),
            "res_model": self._name,
            "res_id": amendment.id,
            "view_mode": "form",
            "target": "current",
        }
