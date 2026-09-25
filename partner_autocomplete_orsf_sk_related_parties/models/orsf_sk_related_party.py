# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One edge of the ownership / officer graph, as it touches one partner."""

from odoo import api, fields, models


class L10nSkRelatedParty(models.Model):
    _name = "orsf.sk.related.party"
    _description = "SK Related Party (závislá osoba)"
    _order = "degree, related_name"

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        ondelete="cascade",
        index=True,
    )
    related_partner_id = fields.Many2one(
        "res.partner",
        string="Related contact",
        ondelete="set null",
        help="The counterpart, when it already exists in this database. Most "
        "related companies do not — the IČO and name below are kept either way.",
    )
    related_ico = fields.Char(string="IČO", index=True)
    related_name = fields.Char(string="Name", required=True)
    link_person = fields.Char(
        string="Through",
        help="The natural person who links the two subjects.",
    )
    link_role = fields.Char(
        string="Role",
        help="The role that person holds, as the register words it — konateľ, "
        "spoločník, člen predstavenstva.",
    )
    degree = fields.Integer(
        string="Degree",
        default=2,
        help="1 = a person holding a role directly in this partner. "
        "2 = another company that person also holds a role in.",
    )
    fetched_at = fields.Datetime(string="Fetched", readonly=True)
    source = fields.Char(string="Source", default="ORSF", readonly=True)

    _partner_related_uniq = models.Constraint(
        "UNIQUE (partner_id, related_ico, link_person, link_role)",
        "This related party is already recorded for this partner.",
    )

    @api.depends("related_name", "related_ico", "link_person")
    def _compute_display_name(self):
        for record in self:
            name = record.related_name or ""
            if record.related_ico:
                name = f"{name} ({record.related_ico})"
            if record.link_person:
                name = f"{name} — {record.link_person}"
            record.display_name = name

    def action_open_related_partner(self):
        self.ensure_one()
        if not self.related_partner_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "res_id": self.related_partner_id.id,
            "view_mode": "form",
        }
