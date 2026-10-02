from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .epostak_connector import INTEGRATOR_SECRET_PREFIX, EpostakApiError


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
    epostak_inbound_fail_activity_after = fields.Integer(
        string="Warn after N failed polls",
        config_parameter="epostak.inbound.fail_activity_after",
        default=3,
        help="After this many consecutive inbound poll failures, raise a to-do "
        "for the EDI manager (or the admin) so someone is told even if nobody "
        "opens this page. It is closed automatically when polling succeeds "
        "again. Set to 0 to never raise one.",
    )
    epostak_sapi_status_tracking = fields.Boolean(
        string="Track Delivery Status",
        config_parameter="epostak.sapi.status_tracking",
        default=True,
        help="Poll the lifecycle endpoint so a sent message advances from "
        "'sent' (accepted for transport) to 'done' (delivered) or 'error'. "
        "Requires the 'documents:read' scope on the Enterprise API.",
    )

    # ------------------------------------------------------------------
    # Inbound health
    # ------------------------------------------------------------------

    epostak_inbound_health = fields.Char(
        string="Last inbound poll",
        compute="_compute_epostak_inbound_health",
        help="Receiving has no other signal: the base poll swallows failures "
        "into the log, so without this a misconfiguration stops inbound "
        "silently while sending still reports errors on the invoice. A stale "
        "timestamp here is the evidence that documents are no longer arriving.",
    )

    def _compute_epostak_inbound_health(self):
        ICP = self.env["ir.config_parameter"].sudo()
        connector = self.env["epostak.connector"]
        for rec in self:
            last_at = ICP.get_param(connector.PARAM_POLL_AT, "")
            last_ok = ICP.get_param(connector.PARAM_POLL_OK, "")
            error = ICP.get_param(connector.PARAM_POLL_ERROR, "")
            count = ICP.get_param(connector.PARAM_POLL_COUNT, "")
            if not last_at:
                rec.epostak_inbound_health = _(
                    "Never polled. Use 'Poll inbound now', or wait for the "
                    "ePošťák inbound cron."
                )
            elif error:
                rec.epostak_inbound_health = _(
                    "FAILED at %(when)s — %(error)s (last success: %(ok)s)",
                    when=last_at,
                    error=error.splitlines()[0][:200],
                    ok=last_ok or _("never"),
                )
            else:
                rec.epostak_inbound_health = _(
                    "OK at %(when)s — %(count)s document(s) fetched",
                    when=last_at,
                    count=count or "0",
                )

    def action_epostak_poll_inbound(self):
        """Poll the mailbox now and say what happened.

        Setting receiving up otherwise means waiting for a cron and then reading
        the server log, because the base poll reports nothing to the user.
        """
        self.ensure_one()
        self.set_values()
        # sudo: this page is gated on base.group_system, but edi.message is
        # restricted to the EDI groups — which an Administrator is not in by
        # default, so the button failed with an AccessError for exactly the
        # person who configures the connection. The work itself is what the
        # inbound cron does as superuser, so running it with the same rights is
        # the behaviour being reproduced, not an escalation of it.
        Message = self.env["edi.message"].sudo()
        connector = self.env["epostak.connector"].sudo()
        ICP = self.env["ir.config_parameter"].sudo()
        before = Message.search_count(
            [("provider", "=", "epostak"), ("direction", "=", "in")]
        )
        Message._get_messages("epostak")
        created = Message.search_count(
            [("provider", "=", "epostak"), ("direction", "=", "in")]
        ) - before
        error = ICP.get_param(connector.PARAM_POLL_ERROR, "")
        errored = Message.search_count([
            ("provider", "=", "epostak"), ("direction", "=", "in"),
            ("state", "=", "error"),
        ])

        if error:
            kind, title = "danger", _("Inbound poll failed")
            message = error
        elif errored:
            kind, title = "warning", _("Polled, but some documents failed")
            message = _(
                "%(created)s new document(s); %(errored)s inbound message(s) "
                "are in error — open EDI Messages to see why.",
                created=created, errored=errored,
            )
        else:
            kind, title = "success", _("Inbound poll OK")
            message = _(
                "%(created)s new document(s) imported.", created=created
            ) if created else _("Nothing new waiting in the mailbox.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": kind,
                "sticky": kind != "success",
                "title": title,
                "message": message,
            },
        }

    # ------------------------------------------------------------------
    # Which kind of key is configured
    # ------------------------------------------------------------------

    epostak_key_kind = fields.Char(
        string="Configured key",
        compute="_compute_epostak_key_kind",
        help="Derived from the secret above, which is write-only in this form. "
        "Without it there is no way to tell from the UI whether the Firm ID "
        "applies, so the help on that field could not be acted on.",
    )

    @api.depends(
        "epostak_mode",
        "epostak_sapi_sandbox_client_secret",
        "epostak_sapi_prod_client_secret",
        "epostak_firm_id",
    )
    def _compute_epostak_key_kind(self):
        """Say outright whether this is an integrator or a firm key.

        The secret renders as a password, so a user cannot see its prefix and
        therefore cannot tell which half of the Firm ID help applies to them.
        A customer hit exactly that on 2026-10-01: an sk_int_* key, the help
        saying "only for integrator keys", no way to know they had one, so the
        Firm ID stayed empty and every call failed 400.
        """
        for rec in self:
            secret = (
                rec.epostak_sapi_prod_client_secret
                if rec.epostak_mode == "production"
                else rec.epostak_sapi_sandbox_client_secret
            ) or ""
            if not secret:
                rec.epostak_key_kind = _("No secret configured yet.")
            elif secret.startswith(INTEGRATOR_SECRET_PREFIX):
                if rec.epostak_firm_id:
                    rec.epostak_key_kind = _(
                        "Integrator key (sk_int_*) — acting for firm %s.",
                        rec.epostak_firm_id,
                    )
                else:
                    rec.epostak_key_kind = _(
                        "Integrator key (sk_int_*) — it speaks for several "
                        "firms, so the ePošťák Firm ID below IS required. Press "
                        "Test Connection to list the firms it may act for."
                    )
            else:
                rec.epostak_key_kind = _(
                    "Firm key (sk_live_*) — the firm is implied by the "
                    "credentials, so leave the ePošťák Firm ID empty."
                )

    def set_values(self):
        """Flush cached access tokens when credentials or URLs change."""
        res = super().set_values()
        self._edi_persist_default_true_booleans(["epostak_sapi_status_tracking"])
        self.env["epostak.connector"]._clear_token_cache()
        return res

    def action_epostak_test_connection(self):
        """Mint a token against the active environment and report the result.

        This button never raises. It is a *report*, and a raised UserError does
        two unwanted things here: it renders as a failure even when the news is
        merely "you still have to pick a firm", and — because the raise rolls
        the transaction back — it silently discards the ``set_values()`` above,
        so a secret the user had just typed is thrown away. Every outcome is a
        notification instead, so what the user entered always persists.
        """
        self.ensure_one()
        # Persist first: the button must test what the user just typed, not
        # the values that were saved before this form was opened.
        self.set_values()
        connector = self.env["epostak.connector"]
        cfg = connector._get_sapi_config()

        def _note(kind, title, message, sticky=True):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": kind,
                    "sticky": sticky,
                    "title": title,
                    "message": message,
                },
            }

        # An integrator key cannot act until it knows which firm it speaks for,
        # and this button is where the user is told so — answer the question
        # rather than restating the error: list the firms and their UUIDs.
        if cfg["client_secret"].startswith(INTEGRATOR_SECRET_PREFIX) and not cfg[
            "firm_id"
        ]:
            try:
                firms = connector._list_firms()
            except EpostakApiError as e:
                return _note(
                    "danger",
                    _("Firm ID required, and the firm list is unavailable"),
                    _(
                        "This is an integrator key (sk_int_*), so the ePošťák "
                        "Firm ID must be set — but the list of firms could not "
                        "be read either: %s",
                        e,
                    ),
                )
            if not firms:
                return _note(
                    "danger",
                    _("Firm ID required, but no firms are available"),
                    _(
                        "This is an integrator key (sk_int_*) and the ePošťák "
                        "Firm ID is empty, but the key reports no firms it may "
                        "act for. Either it is not provisioned for this firm "
                        "yet, or this database should use its own firm key "
                        "(sk_live_*) instead."
                    ),
                )
            if len(firms) == 1:
                # Exactly one firm means there is nothing to choose. Asking the
                # user to copy a UUID across when the answer is already known is
                # busywork, and "this key speaks for several firms" is simply
                # untrue of a key that manages one.
                only = firms[0]
                self.env["ir.config_parameter"].sudo().set_param(
                    "epostak.firm_id", only["id"])
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "success",
                        # Sticky: it names the firm that was chosen on the
                        # user's behalf, which is worth leaving on screen.
                        "sticky": True,
                        "title": _("Firm ID filled in automatically"),
                        "message": _(
                            "This key manages exactly one firm, so the ePošťák "
                            "Firm ID was set to it: %(name)s%(ico)s%(pid)s. Test "
                            "again to confirm the connection.",
                            name=only["name"] or only["id"],
                            ico="  IČO %s" % only["ico"] if only["ico"] else "",
                            pid="  %s" % only["peppol_id"] if only["peppol_id"] else "",
                        ),
                        # soft_reload, NOT reload: the field must refresh or it
                        # keeps showing the empty value we just filled and the
                        # user retypes it — but a full "reload" is a browser
                        # reload, which tore down the notification before it
                        # could be read. Reported: "no popup indicating success
                        # was shown". soft_reload re-renders the action only, so
                        # the toast in the root container survives.
                        "next": {"type": "ir.actions.client", "tag": "soft_reload"},
                    },
                }
            # Bulleted so the list stays readable whether or not the
            # notification preserves the newlines.
            listed = "\n".join(
                "• %s — %s%s%s" % (
                    f["id"],
                    f["name"] or _("(unnamed)"),
                    "  IČO %s" % f["ico"] if f["ico"] else "",
                    "  %s" % f["peppol_id"] if f["peppol_id"] else "",
                )
                for f in firms
            )
            return _note(
                "warning",
                _("Pick a firm: this key manages %s", len(firms)),
                _(
                    "Copy the matching UUID into ePošťák Firm ID and test "
                    "again.\n\n%s",
                    listed,
                ),
            )

        try:
            connector._authenticate()
        except EpostakApiError as e:
            return _note(
                "danger", _("ePošťák connection failed"), "%s" % e
            )
        except UserError as e:
            return _note("danger", _("ePošťák is not configured"), "%s" % e)

        return _note(
            "success",
            _("ePošťák connection OK"),
            _(
                "Authenticated against %(url)s as participant %(pid)s.%(firm)s",
                url=cfg["sapi_url"],
                pid=connector._epostak_own_participant_id() or _("(no Peppol address set)"),
                firm=_("\nActing for firm %s.") % cfg["firm_id"] if cfg["firm_id"] else "",
            ),
            sticky=False,
        )
