# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_sk_par85n = fields.Boolean(
        string="Vehicle VAT limited by § 85n",
        help="The VAT this tax leaves undeducted is the 50 % that § 85n of "
        "the VAT Act withholds on a passenger vehicle. Under § 52zzzk of the "
        "Income Tax Act it is then not a tax expense, and on a purchased "
        "vehicle not part of its tax entry price: the tax depreciation board "
        "leaves it out of the entry value it proposes.",
    )
