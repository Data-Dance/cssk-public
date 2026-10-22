from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    epostak_mode = fields.Selection(
        string="ePošťák Environment",
        selection=[("sandbox", "Sandbox"), ("production", "Production")],
        default="sandbox",
        required=True,
        config_parameter="epostak.mode",
    )
    epostak_firm_id = fields.Char(
        string="ePošťák Firm ID",
        config_parameter="epostak.firm_id",
        help="Only for integrator keys (sk_int_*), which speak for several "
        "firms: the UUID of the TARGET firm we are acting for, sent as the "
        "X-Firm-Id header. This is not the firm_id claim inside the token — "
        "that one identifies the integrator itself and selects nothing. Take "
        "it from GET /api/v1/firms (scope firms:manage). Leave empty for a "
        "firm key (sk_live_*), where the firm is implied by the credentials.",
    )
