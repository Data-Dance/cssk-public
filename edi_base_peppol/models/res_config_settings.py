from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    peppol_auto_send = fields.Boolean(
        string="Auto-send Peppol on Invoice Post",
        config_parameter="peppol.auto_send",
        default=False,
        help="When enabled, every posted customer invoice/credit note whose "
        "customer has a Peppol address is automatically generated as BIS3 UBL "
        "and queued for sending via the installed transport provider. When "
        "off, use the 'Send via Peppol' button on the invoice.",
    )
    peppol_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Peppol Purchase Journal",
        config_parameter="peppol.purchase_journal_id",
        domain="[('type', '=', 'purchase')]",
        help="Journal used to book inbound Peppol vendor bills. Leave empty "
        "to use the company's first purchase journal.",
    )
