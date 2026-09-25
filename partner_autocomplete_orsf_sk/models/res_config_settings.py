# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models

_PARTNER_FIELD_DOMAIN = "[('model_id.model', '=', 'res.partner')]"


class ResConfigSettings(models.TransientModel):
    """Configuration of default values for the ORSF SK autocomplete provider."""

    _inherit = "res.config.settings"

    config_orsf_sk_base_url = fields.Char(
        "ORSF API base URL",
        config_parameter="orsf_sk.base_url",
        help="Leave empty to use https://api.orsf.sk/v1.",
    )
    config_orsf_sk_api_token = fields.Char(
        "ORSF API token",
        config_parameter="orsf_sk.api_token",
        help="Optional Bearer token from your ORSF account. Raises the request "
        "quota and unlocks the full address of a sole trader, which ORSF "
        "otherwise withholds (addressLocked). Anonymous access works without "
        "one. This is an API token, never an account password.",
    )
    config_orsf_sk_login_email = fields.Char(
        "ORSF account e-mail",
        config_parameter="orsf_sk.login_email",
        help="Only the person and graph endpoints need an account; everything "
        "this module does otherwise works anonymously.",
    )
    config_orsf_sk_login_password = fields.Char(
        "ORSF account password",
        config_parameter="orsf_sk.login_password",
        help="ORSF issues no API key for its gated endpoints, so a sign-in is "
        "the only way in. Stored in ir.config_parameter, which is PLAIN TEXT "
        "in the database and in every backup — use a dedicated ORSF account "
        "for this, never a personal one.",
    )
    config_orsf_sk_timeout = fields.Char(
        "Request timeout (s)",
        config_parameter="orsf_sk.timeout",
        help="Seconds to wait for ORSF before giving up. Defaults to 15.",
    )
    orsf_sk_set_company_registry = fields.Boolean(
        related="company_id.orsf_sk_set_company_registry", readonly=False
    )
    orsf_sk_set_company_type = fields.Boolean(
        related="company_id.orsf_sk_set_company_type", readonly=False
    )
    orsf_sk_format_psc = fields.Boolean(
        related="company_id.orsf_sk_format_psc", readonly=False
    )

    orsf_sk_missing_sk_modules = fields.Char(
        string="Missing SK modules",
        compute="_compute_orsf_sk_missing_sk_modules",
        help="Which sibling modules would give these register values a "
        "ready-made field.",
    )

    @api.depends_context("uid")
    def _compute_orsf_sk_missing_sk_modules(self):
        """Name the modules that would supply the fields this is mapping into.

        Detected by the fields themselves rather than by module state, because
        the field is what the mapping actually needs — a module installed but
        not upgraded would report installed and still be missing it.
        """
        partner_fields = self.env["res.partner"]._fields
        owners = {
            "l10n_sk_base": "l10n_sk_dic",
            "l10n_sk_trade_registry": "l10n_sk_register_name",
            "l10n_sk_vat_registration": "l10n_sk_vat_registration_category",
        }
        missing = ", ".join(
            module for module, field in owners.items()
            if field not in partner_fields
        )
        for record in self:
            record.orsf_sk_missing_sk_modules = missing

    # -- dynamic field mappings -------------------------------------------
    # Where each register value is written. These default to the standard SK
    # fields whenever the sibling module that owns them is installed — that is
    # what `Use the standard SK fields` (re)applies, and what the module's
    # post-install hook does automatically. Point one somewhere else and the
    # value follows; clear one and the value is simply not stored.

    config_orsf_sk_mapping_ico = fields.Many2one(
        "ir.model.fields",
        string="IČO",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.ico",
    )
    config_orsf_sk_mapping_dic = fields.Many2one(
        "ir.model.fields",
        string="DIČ",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.dic",
    )
    config_orsf_sk_mapping_nace = fields.Many2one(
        "ir.model.fields",
        string="SK NACE",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.nace",
    )
    config_orsf_sk_mapping_legal_form = fields.Many2one(
        "ir.model.fields",
        string="Právna forma",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.legal_form",
    )
    config_orsf_sk_mapping_register = fields.Many2one(
        "ir.model.fields",
        string="Register",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.register",
    )
    config_orsf_sk_mapping_register_office = fields.Many2one(
        "ir.model.fields",
        string="Registrový súd",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.register_office",
    )
    config_orsf_sk_mapping_register_number = fields.Many2one(
        "ir.model.fields",
        string="Číslo zápisu",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.register_number",
    )
    config_orsf_sk_mapping_status = fields.Many2one(
        "ir.model.fields",
        string="Stav subjektu",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.status",
    )
    config_orsf_sk_mapping_size = fields.Many2one(
        "ir.model.fields",
        string="Veľkostná kategória",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.size",
    )
    config_orsf_sk_mapping_established_date = fields.Many2one(
        "ir.model.fields",
        string="Dátum vzniku",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.established_date",
    )
    config_orsf_sk_mapping_dissolved_date = fields.Many2one(
        "ir.model.fields",
        string="Dátum zániku",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.dissolved_date",
    )
    config_orsf_sk_mapping_vat_registration = fields.Many2one(
        "ir.model.fields",
        string="Druh registrácie DPH (§)",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.vat_registration",
    )
    config_orsf_sk_mapping_vat_payer_since_date = fields.Many2one(
        "ir.model.fields",
        string="Platiteľ DPH od",
        ondelete="set null",
        domain=_PARTNER_FIELD_DOMAIN,
        config_parameter="orsf_sk.mapping.vat_payer_since_date",
    )

    def action_orsf_apply_default_mappings(self):
        """Re-point every mapping at its standard SK field."""
        provider = self.env["partner.autocomplete.provider.orsf_sk"]
        applied = provider._orsf_apply_default_mappings(overwrite=True)
        self.env.user._bus_send("simple_notification", {
            "type": "success" if applied else "warning",
            "title": _("ORSF field mapping"),
            "message": _(
                "%s mappings pointed at their standard SK field. Values whose "
                "field is missing are left unmapped — install the module that "
                "owns them.",
                applied,
            ),
        })
        return {"type": "ir.actions.client", "tag": "reload"}
