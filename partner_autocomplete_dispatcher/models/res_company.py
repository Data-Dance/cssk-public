# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    partner_gid = fields.Char(
        "Company database ID",
        related="partner_id.partner_gid",
        inverse="_inverse_partner_gid",
        store=True,
    )

    partner_autocomplete_provider = fields.Selection(
        selection=lambda self: self.env[
            "res.company"
        ]._selection_partner_autocomplete_provider(),
        string="Autocomplete provider",
        required=True,
        default=lambda self: self.env["partner.autocomplete.provider"]._name,
    )

    def _selection_partner_autocomplete_provider(self):
        return self.env[
            "partner.autocomplete.provider.registry"
        ]._get_available_providers()

    # Following are one2many fields that also can be populated from partner_autocomplete
    child_contact_ids = fields.One2many(related="partner_id.child_ids", readonly=False)
