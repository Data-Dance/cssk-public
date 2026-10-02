# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Purchase order lines follow the company's VAT status on the order date.

Only a proposal: the vendor bill is decided again by its own DUZP
(``l10n_cz_vat_status``).
"""

from odoo import api, fields, models


def _status_day(order, record):
    if order and order.date_order:
        return fields.Date.context_today(record, order.date_order)
    return fields.Date.context_today(record)


def _applies(company):
    return bool(company) and company.account_fiscal_country_id.code == "CZ" \
        and company._l10n_cz_vat_status_has_history()


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            # A line being created in the form has no company of its own yet.
            company = line.order_id.company_id or line.company_id
            if not line.tax_ids or not _applies(company):
                continue
            line.tax_ids = company._l10n_cz_vat_status_map_taxes(
                line.tax_ids,
                company._l10n_cz_vat_status_on(_status_day(line.order_id, line)))

    @api.model
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom,
                                     company_id, partner_id, po):
        """Procurement-generated lines (reordering rules, MTO) too."""
        vals = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, partner_id, po)
        if not _applies(company_id) or not vals.get("tax_ids"):
            return vals
        ids = []
        for command in vals["tax_ids"]:
            if command[0] == 6:
                ids = list(command[2])
            elif command[0] == 4:
                ids.append(command[1])
        taxes = company_id._l10n_cz_vat_status_map_taxes(
            self.env["account.tax"].browse(ids),
            company_id._l10n_cz_vat_status_on(_status_day(po, company_id)))
        vals["tax_ids"] = [(6, 0, taxes.ids)]
        return vals
