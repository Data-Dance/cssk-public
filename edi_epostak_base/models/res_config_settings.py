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
        help="Required when the configured secret is an integrator key "
        "(sk_int_*), which speaks for several firms: the UUID of the TARGET "
        "firm we are acting for, sent as the X-Firm-Id header. Leave empty for "
        "a firm key (sk_live_*), where the firm is implied by the credentials. "
        "The secret is write-only, so check 'Configured key' above to see "
        "which one you have rather than guessing from your contract — a direct "
        "customer can still be issued an integrator key, and then every call "
        "fails with 400 'X-Firm-Id header is required' until this is set. "
        "Press Test Connection to list the firms the key may act for and their "
        "UUIDs. This is NOT the firm_id claim inside the token — that one "
        "identifies the integrator itself and selects nothing.",
    )
