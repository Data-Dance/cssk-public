# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_taxes(self):
        """Product / account default taxes, then the fiscal position, then the
        company's VAT status on the document's DUZP."""
        taxes = super()._get_computed_taxes()
        move = self.move_id
        if taxes and move._l10n_cz_vat_status_applies():
            status = move.company_id._l10n_cz_vat_status_on(
                move._l10n_cz_vat_status_date())
            taxes = move.company_id._l10n_cz_vat_status_map_taxes(taxes, status)
        return taxes

    @api.depends("move_id.taxable_supply_date", "move_id.invoice_date")
    def _compute_cssk_control_section_code(self):
        return super()._compute_cssk_control_section_code()

    def _cssk_resolve_section_code(self):
        """No kontrolní hlášení section for a day the company was no plátce.

        § 101c names only a plátce. An identifikovaná osoba's self-assessed
        acquisition still reports on DPHDP3 ř. 3–6 / 12 / 13, and would
        otherwise be classified into KH A2 like a plátce's; a non-payer's
        bill with non-deductible VAT would land in B2 as if it were deducted.
        """
        move = self.move_id
        if (move and move.company_id.account_fiscal_country_id.code == "CZ"
                and move.company_id._l10n_cz_vat_status_has_history()
                and move.company_id._l10n_cz_vat_status_on(
                    move._l10n_cz_vat_status_date()) != "payer"):
            return False
        return super()._cssk_resolve_section_code()
