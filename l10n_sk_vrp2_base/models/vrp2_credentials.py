import time

from odoo import _, api, fields, models


class Vrp2CredentialsMixin(models.AbstractModel):
    """Shared VRP2 credentials + session state.

    One VRP2 login is bound to exactly one cash register (DKP) — see the login
    response (unitId / cashRegisterId) and the dashboard (single dkp). So this
    mixin represents "one VRP2 cash register" and is inherited by every model
    that needs to authenticate independently:

    - ``res.company`` — the company default register (used by invoice payments)
    - ``pos.config``  — each physical till authenticates as its own register

    ``vrp2.client`` accepts any record inheriting this mixin as its "holder".
    """

    _name = "vrp2.credentials.mixin"
    _description = "VRP2 Credentials & Session"

    # ------------------------------------------------------------------
    # Credentials
    # ------------------------------------------------------------------
    vrp2_login = fields.Char(
        string="VRP2 Login",
        help="Login (kód pokladnice / kód podnikateľa) from Finančná správa SR.",
    )
    vrp2_password = fields.Char(
        string="VRP2 Password",
        groups="base.group_system",
        help="Password for VRP2 authentication.",
    )

    # ------------------------------------------------------------------
    # Session state (written by vrp2.client)
    # ------------------------------------------------------------------
    vrp2_token = fields.Char(
        string="VRP2 Token",
        readonly=True,
        copy=False,
        groups="base.group_system",
        help="Live VRP2 session token — anyone holding it can act on the "
        "cash register, so only administrators may read it.",
    )
    vrp2_role = fields.Selection(
        [("read", "Read"), ("write", "Write")],
        string="VRP2 Role",
        readonly=True,
        copy=False,
    )
    vrp2_return_value = fields.Integer(
        string="VRP2 Return Value", readonly=True, copy=False
    )
    vrp2_last_login = fields.Datetime(
        string="VRP2 Last Login", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # Cached dashboard / cash register info
    # ------------------------------------------------------------------
    vrp2_dkp = fields.Char(
        string="Kód pokladnice (DKP)", readonly=True, copy=False
    )
    vrp2_business_name = fields.Char(
        string="VRP2 Business Name", readonly=True, copy=False
    )
    vrp2_dic = fields.Char(string="DIČ", readonly=True, copy=False)
    vrp2_ico = fields.Char(string="IČO", readonly=True, copy=False)
    vrp2_ic_dph = fields.Char(string="IČ DPH", readonly=True, copy=False)
    vrp2_vat_payer = fields.Boolean(
        string="VRP2 VAT Payer",
        readonly=True,
        copy=False,
        help="The register's organization.vatPayer, as VRP2 reports it. "
        "Sent as vatPayer on every sale receipt.",
    )
    vrp2_register_version = fields.Char(
        string="VRP2 Register Version",
        readonly=True,
        copy=False,
        help="cashRegister.version from the dashboard: a millisecond stamp "
        "of the register's configuration, which moves whenever its settings "
        "are changed in the portal. The web app sends it as the version of "
        "every valid receipt (/v5/receipt/create/valid).",
    )

    # ------------------------------------------------------------------
    # Fiscal rounding ("Zaokrúhľovať na 5 centov")
    # ------------------------------------------------------------------
    vrp2_round_5c = fields.Boolean(
        string="Round to 0.05 €",
        default=True,
        copy=False,
        help="Mirrors the VRP2 web app toggle 'Zaokrúhľovať na 5 centov'. When "
        "on, paid totals are rounded to the nearest 5 cents and the difference "
        "is reported in the receipt's roundingAmount/useRounding.\n"
        "This is a CLIENT-SIDE preference in the VRP2 web app (confirmed: "
        "toggling it sends nothing to the server and never appears in any API "
        "request/response), so it is configured here per register.",
    )

    # ------------------------------------------------------------------
    # Connection status
    # ------------------------------------------------------------------
    vrp2_status = fields.Selection(
        [
            ("not_configured", "Not configured"),
            ("disconnected", "Disconnected"),
            ("connected", "Connected"),
        ],
        string="VRP2 Status",
        compute="_compute_vrp2_status",
        help="Connected = a VRP2 session token is held (the token may still "
        "expire server-side; it is refreshed automatically on the next call).",
    )

    @api.depends("vrp2_login", "vrp2_token")
    def _compute_vrp2_status(self):
        for record in self:
            # sudo: vrp2_token is admin-only, but the (boolean) connection
            # status itself is not sensitive.
            if not record.vrp2_login:
                record.vrp2_status = "not_configured"
            elif record.sudo().vrp2_token:
                record.vrp2_status = "connected"
            else:
                record.vrp2_status = "disconnected"

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def _vrp2_authenticate(self):
        """Login and cache this register's dashboard (cash register + business)."""
        self.ensure_one()
        self.env["vrp2.client"]._login(self)
        self._vrp2_refresh_register()
        return self

    def _vrp2_refresh_register(self):
        """Fetch this register's dashboard and cache its profile.

        Returns the ``cashRegister`` dict. Called at login and again before
        every valid receipt, because the register version it carries changes
        whenever the register is reconfigured in the portal, and a receipt
        must carry the current one.
        """
        self.ensure_one()
        dashboard = self.env["vrp2.client"]._get_dashboard(self)
        cr_data = dashboard.get("cashRegister") or {}
        org_data = cr_data.get("organization") or {}
        # Note: the 5-cent rounding toggle is a client-side preference in the
        # VRP2 web app and is NOT part of the register profile/dashboard, so it
        # is configured locally on the holder (vrp2_round_5c) and never synced.
        version = cr_data.get("version")
        self.sudo().write({
            "vrp2_dkp": cr_data.get("dkp"),
            "vrp2_business_name": org_data.get("name"),
            "vrp2_dic": org_data.get("dic"),
            "vrp2_ico": org_data.get("ico"),
            "vrp2_ic_dph": org_data.get("icDph"),
            "vrp2_vat_payer": bool(org_data.get("vatPayer")),
            "vrp2_register_version": str(version) if version else False,
        })
        return cr_data

    def _vrp2_valid_receipt_header(self):
        """The register-level part of a /v5/receipt/create/valid body.

        Verified against three captures (2026-07-15 invoice storno,
        2026-10-06 sale and sale storno) and the web app's builder:
        ``vatPayer`` is ``cashRegister.organization.vatPayer`` and
        ``version`` is ``cashRegister.version`` — NOT the current time,
        which is what the invoice-payment endpoint takes instead.
        """
        self.ensure_one()
        self._vrp2_refresh_register()
        version = self.vrp2_register_version
        return {
            "vatPayer": self.vrp2_vat_payer,
            "version": int(version) if version else int(time.time() * 1000),
        }

    def _vrp2_logout_session(self):
        self.ensure_one()
        self.env["vrp2.client"]._logout(self)

    def _vrp2_login_notification(self):
        self.ensure_one()
        role_label = dict(
            self._fields["vrp2_role"].selection
        ).get(self.vrp2_role, self.vrp2_role or "")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("VRP2 — Login successful"),
                "message": _(
                    "Connected as %(business)s\nDKP: %(dkp)s\nAccess: %(role)s",
                    business=self.vrp2_business_name or self.vrp2_login,
                    dkp=self.vrp2_dkp or "-",
                    role=role_label,
                ),
                "type": "success",
                "sticky": True,
            },
        }

    # ------------------------------------------------------------------
    # Button actions (available on any holder, e.g. pos.config)
    # ------------------------------------------------------------------

    def action_vrp2_login(self):
        self._vrp2_authenticate()
        return self._vrp2_login_notification()

    def action_vrp2_logout(self):
        self._vrp2_logout_session()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("VRP2"),
                "message": _("Logged out from VRP2."),
                "type": "info",
                "sticky": False,
            },
        }
