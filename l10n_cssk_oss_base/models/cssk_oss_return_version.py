# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CsskOssReturnVersion(models.Model):
    """One statutory form for the OSS return in one member state of identification.

    The shared export pipeline (``cssk.statutory.submission.mixin``) reads the
    template, root element and schema from the record's ``version_id``, the
    same contract the VAT return and the control statement follow. The row
    STRUCTURE is not version data here, unlike the domestic VAT return: an OSS
    return has one row per member state × rate × supply type, an open-ended
    set, so there is no fixed line list to version.
    """

    _name = "cssk.oss.return.version"
    _description = "OSS VAT Return Version"
    _order = "country_id, valid_from desc"

    name = fields.Char(required=True)
    country_id = fields.Many2one(
        "res.country", required=True,
        help="Member state of identification whose tax administration "
             "receives this form.")
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()
    form_code = fields.Char(
        help="The authority's own code for the form, e.g. OSSEI1 (EPO) or "
             "DPOSS_EUv01 (Finančná správa).")
    structure_version = fields.Char(
        help="Structure version the XML declares, where the form carries one "
             "(EPO verzePis). Pinned by hand in the country module's "
             "data/SCHEMA_VERSION: nothing in the XSD can say it is stale.")
    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]")
    xml_schema_data = fields.Binary(attachment=True)
    xml_schema_filename = fields.Char()
    xml_root_element = fields.Char(required=True)
