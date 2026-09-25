# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the register holds about a partner beyond its coordinates.

Three lists, all from the same ORSF company record, all answering questions an
accountant asks about a counterparty and currently has to open a browser for:

``l10n.sk.register.activity``
    Predmety podnikania — the scope of business from ORSR / ŽRSR. **Not the
    same thing as SK NACE.** NACE is one statistical code classifying what a
    company *is*; a predmet podnikania is a legal authorisation to do a
    specific kind of work, and it can lapse or be suspended on its own while
    the company stays active.

``l10n.sk.register.filing``
    Účtovné závierky filed to RÚZ — metadata only. ORSF carries no figures
    (``obsah`` is empty on every výkaz), but *whether* and *when* a customer
    filed is a credit fact that needs no figures.

``l10n.sk.register.history``
    Previous names and registered seats, with the window each was valid for —
    what lets a historic document with an unfamiliar header be reconciled.
"""

from odoo import api, fields, models


class L10nSkRegisterActivity(models.Model):
    _name = "l10n.sk.register.activity"
    _description = "SK Register — predmet podnikania"
    _order = "valid_from desc, id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    name = fields.Text(string="Predmet podnikania", required=True)
    valid_from = fields.Date(string="Platné od")
    valid_to = fields.Date(string="Platné do")
    suspended_from = fields.Date(string="Pozastavené od")
    suspended_to = fields.Date(string="Pozastavené do")
    source = fields.Char(readonly=True)
    is_current = fields.Boolean(
        string="Current",
        compute="_compute_is_current",
        store=True,
        help="Still in force today: begun, not ended, and not under a "
        "suspension that has no end date yet.",
    )

    @api.depends("valid_from", "valid_to", "suspended_from", "suspended_to")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for row in self:
            started = not row.valid_from or row.valid_from <= today
            ended = row.valid_to and row.valid_to < today
            suspended = bool(row.suspended_from) and not row.suspended_to
            row.is_current = bool(started and not ended and not suspended)


class L10nSkRegisterFiling(models.Model):
    _name = "l10n.sk.register.filing"
    _description = "SK Register — účtovná závierka (RÚZ)"
    _order = "period desc, id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    period = fields.Char(string="Obdobie", required=True, index=True)
    filing_type = fields.Char(string="Typ")
    filed_on = fields.Date(string="Dátum podania")
    approved_on = fields.Date(string="Dátum schválenia")
    prepared_on = fields.Date(string="Dátum zostavenia")
    consolidated = fields.Boolean(string="Konsolidovaná")
    source = fields.Char(readonly=True)

    _partner_period_uniq = models.Constraint(
        "UNIQUE (partner_id, period, filing_type)",
        "This filing period is already recorded for this partner.",
    )


class L10nSkRegisterHistory(models.Model):
    _name = "l10n.sk.register.history"
    _description = "SK Register — previous name or seat"
    _order = "valid_to desc, id"

    partner_id = fields.Many2one(
        "res.partner", required=True, ondelete="cascade", index=True
    )
    kind = fields.Selection(
        [("name", "Predchádzajúci názov"), ("address", "Predchádzajúce sídlo")],
        required=True,
    )
    value = fields.Char(string="Znenie", required=True)
    valid_from = fields.Date(string="Platné od")
    valid_to = fields.Date(string="Platné do")
