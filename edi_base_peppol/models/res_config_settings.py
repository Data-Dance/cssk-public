from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # All per company: the settings edit the current company.
    peppol_send_enabled = fields.Boolean(
        related="company_id.peppol_send_enabled", readonly=False)
    peppol_scope = fields.Selection(related="company_id.peppol_scope", readonly=False)
    peppol_auto_send = fields.Boolean(
        related="company_id.peppol_auto_send", readonly=False)
    # Domain repeated: Odoo drops a string domain on a related field.
    peppol_purchase_journal_id = fields.Many2one(
        related="company_id.peppol_purchase_journal_id", readonly=False,
        domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]")

    # Database-wide: one access point carries every company's documents.
    peppol_transport = fields.Selection(
        selection="_selection_peppol_transport",
        string="Peppol Transport",
        config_parameter="peppol.transport",
        help="Which installed EDI provider carries Peppol documents. Needed "
        "only when several are installed: with none chosen then, no document "
        "goes through Peppol and each invoice says why on its Peppol badge. "
        "With a single one installed it is used whatever this says.",
    )

    @api.model
    def _selection_peppol_transport(self):
        # The registered providers that are Peppol transports, so the value
        # stored here always matches an edi.message.provider.
        transports = self.env["account.move"]._peppol_transports()
        return [
            (key, label)
            for key, label in self.env["edi.message"]._selection_provider()
            if key in transports
        ]
