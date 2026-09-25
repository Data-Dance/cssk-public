from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    cssk_ec_summary_code = fields.Char(
        string="EC sales list code",
        help="If set, supplies using this tax are reported on the EC sales "
        "list (Súhrnný výkaz / Souhrnné hlášení) with this transaction code "
        "(SK: 0 = goods, 1 = triangulation, 2 = services).",
    )
