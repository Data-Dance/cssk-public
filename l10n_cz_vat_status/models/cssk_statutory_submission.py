# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Filings ignore a declared later period on a non-payer's documents.

``l10n_cssk_core`` lets ``cssk_vat_deduction_date`` move a document onto a
later DPHDP3 / KH / souhrnné hlášení. For a document dated while the company
was an identifikovaná osoba or a neplátce that date is ignored (see
``account.move._l10n_cz_vat_status_ignores_declared_date``): such a document
belongs to the period it would belong to if the date were empty.

The core rule is not restated here. It is evaluated a second time with the
``cssk_period_ignore_declared_date`` context key, and each affected document
takes its membership from that pass; every other document keeps the answer
of the ordinary one.
"""

from odoo import models


class CsskStatutorySubmissionMixin(models.AbstractModel):
    _inherit = "cssk.statutory.submission.mixin"

    def _cssk_period_move_ids(self, company, date_from, date_to):
        move_ids = super()._cssk_period_move_ids(company, date_from, date_to)
        if (self.env.context.get("cssk_period_ignore_declared_date")
                or company.account_fiscal_country_id.code != "CZ"
                or not company._l10n_cz_vat_status_has_history()):
            return move_ids
        Move = self.env["account.move"]
        # Only a document with a declared date can be affected, and only one
        # the declared date put into this period (its declared date lies in
        # it) or kept out of it (its tax point or accounting date does).
        candidates = Move.search([
            ("company_id", "=", company.id), ("state", "=", "posted"),
            ("cssk_vat_deduction_date", "!=", False),
            "|", "|",
            "&", ("cssk_vat_deduction_date", ">=", date_from),
            ("cssk_vat_deduction_date", "<=", date_to),
            "&", ("taxable_supply_date", ">=", date_from),
            ("taxable_supply_date", "<=", date_to),
            "&", ("date", ">=", date_from), ("date", "<=", date_to),
        ])
        ignored = set(candidates.filtered(
            lambda m: m._l10n_cz_vat_status_ignores_declared_date()).ids)
        if not ignored:
            return move_ids
        undeclared = self.with_context(
            cssk_period_ignore_declared_date=True)._cssk_period_move_ids(
                company, date_from, date_to)
        # Lists throughout, not sets: the order of the ordinary answer is
        # kept, so a filing's lines come out the same on every run.
        kept = [mid for mid in move_ids if mid not in ignored]
        seen = set(kept)
        return kept + [mid for mid in undeclared
                       if mid in ignored and mid not in seen]
