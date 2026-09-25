from odoo import fields, models


class CSSKEcSummaryVersion(models.Model):
    """A versioned EC sales list template (Súhrnný výkaz / Souhrnné hlášení)."""

    _name = "cssk.ec.summary.statement.version"
    _description = "EC Sales List Version"
    _order = "country_id, valid_from desc"

    name = fields.Char(required=True)  # e.g. "SK Súhrnný výkaz 2025"
    country_id = fields.Many2one("res.country", required=True)
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    statement_type_ids = fields.One2many(
        "cssk.ec.summary.statement.type", "version_id"
    )

    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's "
        "statutory XML.",
    )
    xml_schema_data = fields.Binary(attachment=True)
    xml_schema_filename = fields.Char()
    xml_root_element = fields.Char(
        required=True, help="Expected root element, e.g. 'SDV' / 'DPHSHV'."
    )

    allow_monthly = fields.Boolean(default=True)
    allow_quarterly = fields.Boolean(default=True)


class CSSKEcSummaryType(models.Model):
    """Submission type (riadny / opravný / dodatočný)."""

    _name = "cssk.ec.summary.statement.type"
    _description = "EC Sales List Submission Type"
    _order = "version_id, sequence"

    version_id = fields.Many2one(
        "cssk.ec.summary.statement.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    fa_xml_value = fields.Char(
        required=True, help="Value emitted in the statutory XML for this type."
    )
    sequence = fields.Integer(default=10)
