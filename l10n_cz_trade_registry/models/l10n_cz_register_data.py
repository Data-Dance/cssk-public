# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the register holds about a partner beyond its coordinates.

Two lists, both from the subject's entry in the veřejný rejstřík as ARES
republishes it, both answering questions an accountant asks about a
counterparty and currently has to open justice.cz for:

``l10n.cz.register.activity``
    Předmět podnikání, předmět činnosti, doplňková činnost and účel — what the
    entry says the subject does. **Not the same thing as CZ-NACE.** NACE is a
    statistical code classifying what a subject *is*; these are the entry's
    own words, each with the day it was entered and the day it was deleted.

``l10n.cz.register.history``
    Previous names and registered seats, with the window each was valid for —
    what lets a historic document with an unfamiliar header be reconciled.

There is no list of filed financial statements. The Czech ones sit in the
sbírka listin, which ARES does not republish, and a table nothing can fill
would only look like knowledge.
"""

from odoo import api, fields, models

ACTIVITY_KINDS = [
    ("business", "Předmět podnikání"),
    ("activity", "Předmět činnosti"),
    ("secondary", "Doplňková činnost"),
    ("purpose", "Účel"),
]


class L10nCzRegisterActivity(models.Model):
    _name = "l10n.cz.register.activity"
    _description = "CZ Register — předmět podnikání nebo činnosti"
    _order = "valid_to desc, valid_from desc, id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    kind = fields.Selection(
        ACTIVITY_KINDS, string="Druh", required=True, default="business"
    )
    name = fields.Text(string="Znění", required=True)
    valid_from = fields.Date(string="Zapsáno")
    valid_to = fields.Date(string="Vymazáno")
    source = fields.Char(readonly=True)
    is_current = fields.Boolean(
        string="Current",
        compute="_compute_is_current",
        store=True,
        help="Still entered today: entered, and not deleted since.",
    )

    @api.depends("valid_from", "valid_to")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for row in self:
            started = not row.valid_from or row.valid_from <= today
            ended = row.valid_to and row.valid_to <= today
            row.is_current = bool(started and not ended)


class L10nCzRegisterHistory(models.Model):
    _name = "l10n.cz.register.history"
    _description = "CZ Register — previous name or seat"
    _order = "valid_to desc, id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    kind = fields.Selection(
        [("name", "Předchozí název"), ("address", "Předchozí sídlo")],
        required=True,
    )
    value = fields.Char(string="Znění", required=True)
    valid_from = fields.Date(string="Zapsáno")
    valid_to = fields.Date(string="Vymazáno")
