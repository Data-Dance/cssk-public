# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""An order is not a tax document, so its date only PROPOSES taxes.

The invoice made from it is decided again by its own DUZP
(``l10n_cz_vat_status``), and refuses to post if the order's taxes no longer
fit — an order confirmed in June and invoiced in July across a registration
gets its taxes corrected on the invoice, not here.
"""

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_tax_ids(self):
        super()._compute_tax_ids()
        for line in self:
            # A line being created in the form has no company of its own yet.
            company = line.order_id.company_id or line.company_id
            if (not line.tax_ids or not company
                    or company.account_fiscal_country_id.code != "CZ"
                    or not company._l10n_cz_vat_status_has_history()):
                continue
            order = line.order_id
            day = (fields.Date.context_today(order, order.date_order)
                   if order.date_order else fields.Date.context_today(line))
            line.tax_ids = company._l10n_cz_vat_status_map_taxes(
                line.tax_ids, company._l10n_cz_vat_status_on(day))
