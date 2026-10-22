from odoo import fields, models
# 18.0: the core class is ``Partner``. Odoo 19 renamed the model classes to
# match their model names (``Partner`` -> ``ResPartner``), so importing the
# 19.0 name here fails at import time with a bare ImportError.
from odoo.addons.base.models.res_partner import Partner as BaseResPartner


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Let the standard name search / autocomplete also match a partner by
    # its GLN. Reference the base list so we stay in sync if Odoo changes it.
    _rec_names_search = BaseResPartner._rec_names_search + ["global_location_number"]

    edi_communication_partner_id = fields.Many2one(
        "res.partner",
        string="EDI Communication Endpoint",
        help="The partner whose GLN owns the EDI transport mailbox "
        "(e.g. eXite for Editel). Used for the BizTalk envelope "
        "<from>/<to> identification, while role-specific party blocks "
        "(buyer, invoicee, delivery_place) use the partner's own GLN.\n\n"
        "Cascades via commercial_partner_id: set this once on the legal "
        "entity (the commercial partner) and all sub-contacts inherit. "
        "When empty, the partner's own GLN is used — single-GLN customers "
        "(the common case) don't need to configure it.",
    )

    edi_desadv_sscc_mode = fields.Boolean(
        string="EDI DESADV in SSCC mode",
        help="When set, outbound DESADV for this customer uses the SSCC "
        "package structure (Editel x11-DESADV-01b-sscc schema) instead "
        "of the flat article list. METRO and a handful of other retailers "
        "require this mode for dock-side automation.\n\n"
        "Cascades via commercial_partner_id: set on the legal entity, all "
        "sub-contacts inherit.",
    )

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

    def _edi_use_sscc_desadv(self):
        """True when outbound DESADV for this partner should use the
        SSCC package structure. Cascades via commercial_partner_id so
        a single setting on the legal entity applies to all delivery
        / invoice sub-contacts under it."""
        self.ensure_one()
        return self.commercial_partner_id.edi_desadv_sscc_mode

    def _edi_envelope_partner(self):
        """Return the partner whose GLN identifies this contact in the
        BizTalk envelope (the eXite mailbox owner).

        Cascades via commercial_partner_id so the field only needs to be
        set on the legal entity. For customers whose mailbox GLN equals
        their legal-entity GLN (the common case) the result is just the
        commercial partner; for split-identity senders (METRO, etc.) it
        resolves to a separate mailbox-owning partner.
        """
        self.ensure_one()
        cp = self.commercial_partner_id
        return cp.edi_communication_partner_id or cp

    product_edi_code_priority = fields.Selection(
        string="EDI Product Code Priority",
        selection=[
            (
                "default_code__barcode__supplier_code",
                "Default Code, Barcode, Supplier Code",
            ),
            (
                "default_code__supplier_code__barcode",
                "Default Code, Supplier Code, Barcode",
            ),
            (
                "barcode__default_code__supplier_code",
                "Barcode, Default Code, Supplier Code",
            ),
            (
                "barcode__supplier_code__default_code",
                "Barcode, Supplier Code, Default Code",
            ),
            (
                "supplier_code__default_code__barcode",
                "Supplier Code, Default Code, Barcode",
            ),
            (
                "supplier_code__barcode__default_code",
                "Supplier Code, Barcode, Default Code",
            ),
        ],
        default="barcode__supplier_code__default_code",
        help="Priority order for matching incoming EDI article codes to "
        "products. Shared by all EDI providers (Editel, GRiT, ...).",
    )
