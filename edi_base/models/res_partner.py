from odoo import fields, models
from odoo.addons.base.models.res_partner import ResPartner as BaseResPartner


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Let the standard name search / autocomplete also match a partner by
    # its GLN. Reference the base list so we stay in sync if Odoo changes it.
    _rec_names_search = BaseResPartner._rec_names_search + ["global_location_number"]

    edi_auto_send_override = fields.Boolean(
        string="Override EDI auto-send",
        help="Enable per-message-type overrides of the global auto-send "
        "configuration for this customer/vendor. When off (the default), "
        "outbound EDI messages follow the global ir.config_parameter "
        "values. When on, each provider module exposes per-message-type "
        "Selection fields (`always` / `never` / `default`) that take "
        "precedence over the global setting for this commercial partner.",
    )

    def _edi_resolve_auto_send(self, override_field_name, config_param):
        """Generic resolver used by all provider auto-send helpers.

        Reads the per-partner Selection override (`always` / `never` /
        `default`) from the commercial partner, cascading. When the
        override is `default` (or `edi_auto_send_override` is off on the
        commercial partner), falls through to the global ir.config_parameter.
        """
        self.ensure_one()
        cp = self.commercial_partner_id
        if cp.edi_auto_send_override and override_field_name in cp._fields:
            override = getattr(cp, override_field_name)
            if override == "always":
                return True
            if override == "never":
                return False
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(config_param, "True")
            .lower()
            not in ("0", "false")
        )
