import logging
from datetime import timedelta

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    cssk_vat_deduction_date = fields.Date(
        string="VAT period declared",
        copy=False,
        index=True,
        help="Period in which the input-VAT deduction is exercised, when that "
        "differs from the accounting date. CZ § 73 and the SK equivalent allow "
        "the deduction to be claimed later than the supply — typically in the "
        "period the document is received — and the return must then report it "
        "in that later period.\n\n"
        "Also honoured on the OUTPUT side, where it names the period a supply "
        "was actually declared in rather than its tax point — a § 42 "
        "correction is declared when the corrective document reaches the "
        "customer, and a document entered late is declared in the period of "
        "entry. Empty is the normal case there and the tax point governs, so "
        "a document raised in Odoo behaves exactly as before.\n\n"
        "Leave empty for the normal case, where a bill is booked in the period "
        "it is claimed: the accounting date is then used. It matters for "
        "documents booked in one period and claimed in another, and for "
        "accounting history imported from a system that records the two dates "
        "separately.",
    )

    def _cssk_rate_date(self):
        """The date whose VAT rates governed this document.

        **Not the period date, and the difference is the whole point.**
        ``_cssk_period_move_ids`` answers "which period reports this", and on
        the input side that is deliberately the date the deduction is
        *exercised* — which CZ § 73 and the SK equivalent allow to be months
        after the supply, and therefore, at a rate change, in a different rate
        regime. The RATE is fixed when the tax point arises: a supply of
        December 2024 is taxed at 20 % however late the deduction is claimed.

        So this reads the tax point where the document records one and the
        accounting date otherwise, and it deliberately ignores
        ``cssk_vat_deduction_date`` — that field names a period, never a rate.
        Feeding the period date into a rate lookup would misrate exactly the
        documents that straddle a rate change, which are the only ones where
        any of this matters.

        Unlike ``CSSK_TAX_POINT_MOVE_TYPES``, no move type is excluded here.
        That constant exists because the period basis differs between output
        and input; the rate does not — the supply date determines it on both
        sides, so a vendor bill that records one is rated by it.

        ``taxable_supply_date`` is core in Odoo 19 but came from the country
        modules in 18.0, so its presence is checked rather than assumed.
        """
        self.ensure_one()
        if "taxable_supply_date" in self._fields:
            return self.taxable_supply_date or self.date
        return self.date

    #: Slack around the dates the period rule can possibly key on, for the
    #: candidate search only. One statutory period either side is enough once
    #: the anchors below are right; it was 400 days forward when the anchor was
    #: the tax point alone, which made the search drag in a year of filings and
    #: ask each of them a question costing several full-table move searches.
    CSSK_FOOTPRINT_WINDOW = 62      # days

    #: Refuse to expand rather than grind. Reached only if the anchors are
    #: wrong or a company files far more often than any statute requires, and a
    #: silent partial answer here would read as "not on any filing".
    CSSK_FOOTPRINT_MAX_CANDIDATES = 40

    def _cssk_footprint_anchor_dates(self):
        """Every date the period rule can key on for this document.

        Not one date, because the rule does not use one. ``_cssk_period_move_ids``
        reads the tax point for the output side, the accounting date for the
        claim side, and ``cssk_vat_deduction_date`` in preference to either
        where it is set — which is exactly the case that puts a December supply
        on a March return. Anchoring the candidate window on the tax point
        alone therefore missed late-claimed documents unless the window was
        stretched to a year, so it takes all three and spans them.
        """
        self.ensure_one()
        dates = {d for d in (self._cssk_rate_date(), self.date,
                             self.cssk_vat_deduction_date) if d}
        return (min(dates), max(dates)) if dates else (None, None)

    def _cssk_footprint_filings(self, res_model):
        """Filings of ``res_model`` that actually report this document.

        **Asks the filing, rather than deciding here.** Which period reports a
        document is not a date comparison: the basis differs between the
        output and the input side, a deduction may be exercised periods after
        the supply, and ``cssk_vat_deduction_date`` overrides the tax point on
        both sides. ``_cssk_period_move_ids`` on the submission mixin is the
        one implementation of that rule, and restating it here would make this
        a second reader of it — the exact failure that has already cost this
        codebase a VAT-return footprint that reported no DPH row at all, and
        that the tag-formula parser's own docstring warns about ("ONE parser
        for the grammar, because two read it… They had drifted").

        So the date window is a pre-filter and nothing more: it decides which
        filings are worth ASKING, and each one then answers for itself. That
        asking is not free — each answer costs two or three searches over
        account.move and materialises every move id in the period — so the
        window is kept tight by anchoring it on the dates the rule can
        actually key on rather than by guessing generously.
        """
        self.ensure_one()
        if res_model not in self.env:
            return self.env["account.move"].browse()
        Model = self.env[res_model]
        if not hasattr(Model, "_cssk_period_move_ids"):
            return Model.browse()
        lo, hi = self._cssk_footprint_anchor_dates()
        if not lo:
            return Model.browse()
        slack = timedelta(days=self.CSSK_FOOTPRINT_WINDOW)
        candidates = Model.search(
            [("company_id", "=", self.company_id.id),
             ("date_to", ">=", lo - slack), ("date_from", "<=", hi + slack)],
            limit=self.CSSK_FOOTPRINT_MAX_CANDIDATES + 1)
        if len(candidates) > self.CSSK_FOOTPRINT_MAX_CANDIDATES:
            _logger.warning(
                "cssk footprint: %s has more than %d candidate %s filings "
                "around %s; not resolving, the link is left blank rather than "
                "answered from part of the set.",
                self.name, self.CSSK_FOOTPRINT_MAX_CANDIDATES, res_model, lo)
            return Model.browse()
        hit = Model.browse()
        for filing in candidates:
            move_ids = filing._cssk_period_move_ids(
                filing.company_id, filing.date_from, filing.date_to)
            if self.id in set(move_ids):
                hit |= filing
        return hit

    def action_cssk_statutory_footprint(self):
        """Reverse drill: list the statutory report rows this document feeds,
        aggregated over its journal items and de-duplicated."""
        self.ensure_one()
        seen = set()
        rows = []
        resolved = {}
        for line in self.line_ids:
            for fp in line._cssk_statutory_footprint():
                key = (fp["form"], fp["code"])
                if key in seen:
                    continue
                seen.add(key)
                vals = {"form": fp["form"], "code": fp["code"],
                        "name": fp.get("name", "")}
                # ``res_model`` is OPTIONAL in the footprint contract. A
                # contributor that does not supply it produces a row with no
                # filing link and nothing else changes — which is what keeps
                # this from being a breaking change across six modules that
                # have drifted from each other before.
                res_model = fp.get("res_model")
                if res_model and fp.get("res_id"):
                    # A contributor that reached the row THROUGH the filing
                    # already knows which one. Resolving it again would be
                    # both wasted work and a chance to disagree with it.
                    record = self.env[res_model].browse(fp["res_id"])
                    vals.update(filing_res_model=res_model,
                                filing_res_id=record.id, filing_count=1,
                                filing_name=record.display_name)
                elif res_model:
                    if res_model not in resolved:
                        resolved[res_model] = self._cssk_footprint_filings(
                            res_model)
                    filings = resolved[res_model]
                    vals.update(
                        filing_res_model=res_model,
                        filing_count=len(filings),
                        filing_res_id=filings.id if len(filings) == 1 else 0,
                        filing_name=(
                            filings.display_name if len(filings) == 1
                            else _("%s filings cover this period",
                                   len(filings)) if filings else False),
                    )
                rows.append((0, 0, vals))
        wizard = self.env["cssk.statutory.footprint.wizard"].create({
            "move_id": self.id, "line_ids": rows})
        return {
            "type": "ir.actions.act_window",
            "name": _("Statutory footprint — %s") % (self.name or ""),
            "res_model": "cssk.statutory.footprint.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    # NB: the CZ/SK payment symbols (VS/KS/SS) historically lived here; they
    # moved to the dedicated l10n_cssk_payment_symbols module, which also owns
    # their validation, credit-note policy and statement-line counterparts.
    # Core no longer depends on it: a module that uses the symbols declares
    # l10n_cssk_payment_symbols itself.
