from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Sandbox environment
    epostak_sapi_sandbox_base_url = fields.Char(
        string="SAPI Sandbox URL",
        config_parameter="epostak.sapi.sandbox.base_url",
        default="https://dev.epostak.sk/sapi/v1",
    )
    epostak_sapi_sandbox_client_id = fields.Char(
        string="Sandbox Client ID",
        config_parameter="epostak.sapi.sandbox.client_id",
    )
    epostak_sapi_sandbox_client_secret = fields.Char(
        string="Sandbox Client Secret",
        config_parameter="epostak.sapi.sandbox.client_secret",
    )
    epostak_api_sandbox_base_url = fields.Char(
        string="Enterprise API Sandbox URL",
        config_parameter="epostak.api.sandbox.base_url",
        default="https://dev.epostak.sk/api/v1",
        help="Used only for delivery-status and participant-capability "
        "lookups, which SAPI does not provide.",
    )

    # Production environment
    epostak_sapi_prod_base_url = fields.Char(
        string="SAPI Production URL",
        config_parameter="epostak.sapi.prod.base_url",
        default="https://epostak.sk/sapi/v1",
    )
    epostak_sapi_prod_client_id = fields.Char(
        string="Production Client ID",
        config_parameter="epostak.sapi.prod.client_id",
    )
    epostak_sapi_prod_client_secret = fields.Char(
        string="Production Client Secret",
        config_parameter="epostak.sapi.prod.client_secret",
    )
    epostak_api_prod_base_url = fields.Char(
        string="Enterprise API Production URL",
        config_parameter="epostak.api.prod.base_url",
        default="https://epostak.sk/api/v1",
        help="Used only for delivery-status and participant-capability "
        "lookups, which SAPI does not provide.",
    )

    # Tuning
    epostak_sapi_scope = fields.Char(
        string="OAuth Scope",
        config_parameter="epostak.sapi.scope",
        default="documents:send documents:read documents:write",
        help="Space-separated scopes requested when minting a token. "
        "'documents:send' alone allows sending but not inbound polling or "
        "delivery-status tracking.",
    )
    epostak_sapi_timeout = fields.Integer(
        string="Request Timeout (s)",
        config_parameter="epostak.sapi.timeout",
        default=60,
    )
    epostak_sapi_limit = fields.Integer(
        string="Documents per Poll Page",
        config_parameter="epostak.sapi.limit",
        default=20,
        help="Page size for the inbound listing. The API accepts 1 to 100.",
    )
    epostak_sapi_max_pages = fields.Integer(
        string="Max Pages per Poll",
        config_parameter="epostak.sapi.max_pages",
        default=5,
        help="Upper bound on pages fetched in one poll. When the mailbox "
        "still has more, the inbound cron is re-triggered to continue.",
    )
    epostak_sapi_status_tracking = fields.Boolean(
        string="Track Delivery Status",
        config_parameter="epostak.sapi.status_tracking",
        default=True,
        help="Poll the lifecycle endpoint so a sent message advances from "
        "'sent' (accepted for transport) to 'done' (delivered) or 'error'. "
        "Requires the 'documents:read' scope on the Enterprise API.",
    )

    def set_values(self):
        """Flush cached access tokens when credentials or URLs change."""
        res = super().set_values()
        self._edi_persist_default_true_booleans(["epostak_sapi_status_tracking"])
        self.env["epostak.connector"]._clear_token_cache()
        return res

    def action_epostak_test_connection(self):
        """Mint a token against the active environment and report the result."""
        self.ensure_one()
        # Persist first: the button must test what the user just typed, not
        # the values that were saved before this form was opened.
        self.set_values()
        connector = self.env["epostak.connector"]
        connector._authenticate()
        cfg = connector._get_sapi_config()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "sticky": False,
                "title": _("ePošťák connection OK"),
                "message": _(
                    "Authenticated against %(url)s as participant %(pid)s.",
                    url=cfg["sapi_url"],
                    pid=connector._epostak_own_participant_id(),
                ),
            },
        }
