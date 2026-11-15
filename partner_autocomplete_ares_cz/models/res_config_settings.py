# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration of default values for Partner Autocomplete Provider."""

    _inherit = "res.config.settings"

    config_ares_cz_mapping_ico = fields.Many2one(
        "ir.model.fields",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.ico",
    )
    config_ares_cz_mapping_nace = fields.Many2one(
        "ir.model.fields",
        string="Prevailing activity (CZ-NACE 2025)",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.nace",
        help="Partner field receiving the prevailing activity from the "
        "statistical register (RES). Costs one more ARES request per lookup; "
        "empty: not fetched.",
    )

    # Where ARES's copy of the veřejný rejstřík is written. These default to
    # the fields of l10n_cz_trade_registry wherever that module is installed;
    # point one elsewhere and the value follows, clear one and it is not
    # stored.
    config_ares_cz_mapping_register = fields.Many2one(
        "ir.model.fields",
        string="Rejstřík",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.register",
        help="Partner field receiving the name of the register the subject "
        "is entered in. The register coordinates cost one more ARES request "
        "per lookup; with all three empty it is not made.",
    )
    config_ares_cz_mapping_register_office = fields.Many2one(
        "ir.model.fields",
        string="Rejstříkový soud",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.register_office",
    )
    config_ares_cz_mapping_register_number = fields.Many2one(
        "ir.model.fields",
        string="Spisová značka",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.register_number",
        help="Oddíl and vložka, e.g. C 12345.",
    )
    config_ares_cz_mapping_status = fields.Many2one(
        "ir.model.fields",
        string="Register status",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.status",
    )
    config_ares_cz_mapping_established_date = fields.Many2one(
        "ir.model.fields",
        string="Datum vzniku",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner'), ('ttype', '=', 'date')]",
        config_parameter="ares_cz.mapping.established_date",
    )
    config_ares_cz_mapping_dissolved_date = fields.Many2one(
        "ir.model.fields",
        string="Datum zániku",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner'), ('ttype', '=', 'date')]",
        config_parameter="ares_cz.mapping.dissolved_date",
    )
