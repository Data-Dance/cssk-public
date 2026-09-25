# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    l10n_sk_reverse_charge = fields.Boolean(
        string="SK Reverse Charge (§69/12)",
        help="This tax represents a domestic reverse-charge supply (prenesenie "
        "daňovej povinnosti). When used on an invoice line, the mandatory "
        "§69 ods. 12 phrase is printed on the SK invoice.",
    )
