# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

_KH_CODE_HELP = (
    "Commodity code for the VAT control statement (§92a reverse charge), "
    "reported in sections A.1 (supplier) and B.1 (customer). E.g. 1 = gold, "
    "3 = supply of immovable property, 4 = construction or assembly work, "
    "5 = goods listed in Annex 5, 6 = emission allowances, 11–21 = other "
    "(mobile phones, microprocessors, cereals, metals, …). Set it on the "
    "reverse-charge tax or on the product."
)


class AccountTax(models.Model):
    _inherit = "account.tax"

    cssk_kh_commodity_code = fields.Char(
        string="KH commodity code (§92a)", help=_KH_CODE_HELP)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cssk_kh_commodity_code = fields.Char(
        string="KH commodity code (§92a)", help=_KH_CODE_HELP)
