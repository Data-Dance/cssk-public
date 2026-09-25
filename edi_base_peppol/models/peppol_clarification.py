from odoo import api, fields, models


class PeppolClarification(models.Model):
    _name = "edi.peppol.clarification"
    _description = "Peppol clarification code (Invoice Response reason/action)"
    _order = "list_identifier, code"

    list_identifier = fields.Selection(
        [
            ("OPStatusReason", "Status reason"),
            ("OPStatusAction", "Status action"),
        ],
        string="List",
        required=True,
        help="Which Peppol clarification list this code belongs to — a reason "
        "for the response status, or a requested action.",
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)
    description = fields.Char(translate=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s — %s" % (rec.code, rec.name) if rec.code else rec.name
