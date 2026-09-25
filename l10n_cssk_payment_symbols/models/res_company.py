# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cssk_refund_vs_policy = fields.Selection(
        [
            ("own", "Credit note's own number"),
            ("origin", "Original invoice's variable symbol"),
        ],
        string="Credit Note Variable Symbol",
        default="own",
        required=True,
        help="Which variable symbol a customer credit note carries: its own "
        "document number (default), or the variable symbol of the "
        "invoice it reverses (common where customers net payments by "
        "the original symbol).",
    )
    l10n_cssk_default_constant_symbol = fields.Char(
        string="Default Constant Symbol",
        size=4,
        help="Constant symbol preset on customer documents "
        "(e.g. 0008 goods, 0308 services). Leave empty for none.",
    )
    l10n_cssk_payment_reference_use_vs = fields.Boolean(
        string="Payment Reference = Variable Symbol",
        help="On posting, customer documents use the variable symbol as "
        "their payment reference — core QR codes, UBL payment IDs and "
        "bank matching then carry the symbol automatically. Does not "
        "change already-posted documents.",
    )
