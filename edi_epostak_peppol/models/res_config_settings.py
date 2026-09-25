from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    peppol_transport = fields.Selection(
        selection="_selection_peppol_transport",
        string="Peppol Transport",
        config_parameter="peppol.transport",
        help="Which installed EDI provider carries Peppol documents. Only "
        "matters when several transports are installed at once; leave empty "
        "to use ePošťák.",
    )

    @api.model
    def _selection_peppol_transport(self):
        # Offer exactly the providers registered on edi.message, so the value
        # stored here can always be matched against edi.message.provider.
        return self.env["edi.message"]._selection_provider()
