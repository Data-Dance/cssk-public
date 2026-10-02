# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One row of the company's VAT-status history.

The history is a list of **change points**, not of intervals: each row says
"from this day on, the company was X". A row ends the day before the next one
starts, so the history can have neither a gap nor an overlap, and every date
has exactly one answer. Dates before the first row are a plátce — the same
answer as no history at all, which is what keeps a database that never records
anything exactly where it was.

Which day to enter is the whole difficulty, because the Act words each
transition differently. ``legal_basis`` + ``event_date`` propose it:

======================  ===================================  ==================
basis                   the Act                               status from
======================  ===================================  ==================
§ 6 odst. 1             plátce from 1 January of the next      1. 1. of year+1
                        year after the turnover year
§ 6 odst. 2             plátce "dnem následujícím" after the   event + 1 day
                        threshold was exceeded
§ 6f / § 94a            voluntary: "ode dne následujícího      event + 1 day
                        po dni oznámení rozhodnutí"
§ 6g / § 6h / § 6i      identifikovaná osoba "ode dne" of      event
                        the first acquisition / receipt /
                        supply
§ 6j–§ 6l / § 97a       voluntary IO: day after oznámení       event + 1 day
§ 107b odst. 5          a plátce deregistered on request       event
                        becomes IO "dnem, kdy přestal být
                        plátcem"
§ 106 odst. 8 písm. a)  ex officio deregistration: ceases      event
                        "dnem nabytí právní moci"
§ 107b odst. 3          on request: ceases "dnem               event + 1 day
                        následujícím po dni oznámení"
§ 106b                  zánik registrace: ceases the day       event
                        before the registration / membership
                        (event = that day)
§ 107 odst. 3           IO deregistered ex officio: právní     event
                        moc
§ 107b odst. 4          IO deregistered on request: day        event + 1 day
                        after oznámení
======================  ===================================  ==================

§ 95 is repealed in the current wording; mandatory registration is § 94 and
voluntary § 94a, but for a § 6 plátce the status arises by law on the day
above, whatever the date of the registration decision.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

STATUSES = [
    ("payer", "Plátce DPH (§ 6–6f)"),
    ("identified", "Identifikovaná osoba (§ 6g–6l)"),
    ("non_payer", "Neplátce"),
]

#: code -> (status it belongs to, label, rule for date_from from event_date)
#: Rules: "next_day" event + 1, "same_day" event, "next_year" 1. 1. of the
#: year after the event, None no proposal.
LEGAL_BASES = {
    "payer_6_1": ("payer",
                  "§ 6 odst. 1 – obrat překročen, plátce od 1. 1.", "next_year"),
    "payer_6_2": ("payer",
                  "§ 6 odst. 2 – obrat překročen, plátce dnem následujícím",
                  "next_day"),
    "payer_6f": ("payer",
                 "§ 6f / § 94a – dobrovolná registrace (den po oznámení)",
                 "next_day"),
    "payer_other": ("payer", "§ 6a–6ea – jiný důvod", None),
    "identified_6g": ("identified",
                      "§ 6g – první pořízení zboží z jiného členského státu",
                      "same_day"),
    "identified_6h": ("identified",
                      "§ 6h – přijetí plnění od osoby neusazené v tuzemsku",
                      "same_day"),
    "identified_6i": ("identified",
                      "§ 6i – poskytnutí služby do jiného členského státu "
                      "(§ 9 odst. 1)", "same_day"),
    "identified_6k_6l": ("identified",
                         "§ 6j–6l / § 97a – registrace na přihlášku (den po "
                         "oznámení)", "next_day"),
    "identified_107b_5": ("identified",
                          "§ 107b odst. 5 – po zrušení registrace plátce",
                          "same_day"),
    "non_payer_initial": ("non_payer", "Nikdy nebyl registrován", None),
    "non_payer_106_8": ("non_payer",
                        "§ 106 odst. 8 písm. a) – zrušení registrace z moci "
                        "úřední (právní moc)", "same_day"),
    "non_payer_107b_3": ("non_payer",
                         "§ 107b odst. 3 – zrušení registrace na žádost (den "
                         "po oznámení)", "next_day"),
    "non_payer_106b": ("non_payer", "§ 106b – zánik registrace plátce",
                       "same_day"),
    "non_payer_107_3": ("non_payer",
                        "§ 107 odst. 3 – zrušení registrace identifikované "
                        "osoby z moci úřední (právní moc)", "same_day"),
    "non_payer_107b_4": ("non_payer",
                         "§ 107b odst. 4 – zrušení registrace identifikované "
                         "osoby na žádost (den po oznámení)", "next_day"),
}


class L10nCzVatStatusPeriod(models.Model):
    _name = "l10n.cz.vat.status.period"
    _description = "CZ company VAT status (from date)"
    _order = "company_id, date_from"
    _rec_name = "status"

    company_id = fields.Many2one(
        "res.company", required=True, index=True, ondelete="cascade",
        default=lambda self: self.env.company)
    date_from = fields.Date(
        string="Valid from", required=True,
        help="First day the status applies. It applies until the day before "
        "the next row's date. Enter the day the Act names, which is not "
        "always the date of the decision — see Legal basis.")
    date_to = fields.Date(
        string="Valid until", compute="_compute_date_to",
        help="The day before the next row starts; empty for the current one.")
    status = fields.Selection(STATUSES, string="VAT status", required=True)
    legal_basis = fields.Selection(
        [(code, spec[1]) for code, spec in LEGAL_BASES.items()],
        string="Legal basis",
        help="Why the status changed. Together with the event date it proposes "
        "the first day of the new status, since the Act words each transition "
        "differently (dnem / dnem následujícím / od 1. ledna).")
    event_date = fields.Date(
        string="Event date",
        help="The day the Act counts from: the day the turnover was exceeded, "
        "the day the decision was notified (oznámení), the day it became "
        "final (právní moc), or the day of the first acquisition or supply.")
    decision_ref = fields.Char(
        string="Č. j. rozhodnutí",
        help="Reference of the tax office's decision, where there is one.")
    note = fields.Text()

    _company_date_uniq = models.Constraint(
        "UNIQUE (company_id, date_from)",
        "The company already has a VAT status starting on that day.",
    )

    @api.depends("date_from", "company_id.l10n_cz_vat_status_period_ids.date_from")
    def _compute_date_to(self):
        for rec in self:
            later = rec.company_id.l10n_cz_vat_status_period_ids.filtered(
                lambda p: rec.date_from and p.date_from
                and p.date_from > rec.date_from)
            nxt = min(later.mapped("date_from")) if later else False
            rec.date_to = nxt - relativedelta(days=1) if nxt else False

    @api.onchange("legal_basis", "event_date")
    def _onchange_legal_basis(self):
        spec = LEGAL_BASES.get(self.legal_basis)
        if not spec:
            return
        self.status = spec[0]
        if self.event_date:
            proposed = self._propose_date_from(self.legal_basis, self.event_date)
            if proposed:
                self.date_from = proposed

    @api.model
    def _propose_date_from(self, legal_basis, event_date):
        """The first day of the new status, as the Act words it."""
        rule = LEGAL_BASES.get(legal_basis, (None, None, None))[2]
        if not event_date or not rule:
            return False
        if rule == "next_day":
            return event_date + relativedelta(days=1)
        if rule == "next_year":
            return event_date.replace(month=1, day=1) + relativedelta(years=1)
        return event_date

    @api.constrains("status", "legal_basis")
    def _check_legal_basis(self):
        for rec in self:
            spec = LEGAL_BASES.get(rec.legal_basis)
            if spec and spec[0] != rec.status:
                raise ValidationError(self.env._(
                    "The legal basis “%(basis)s” does not lead to the status "
                    "“%(status)s”.",
                    basis=spec[1],
                    status=dict(STATUSES)[rec.status]))

    # ------------------------------------------------------------------
    # A change of history re-decides documents already posted: which taxes
    # the next document gets, and which posted lines belong in a kontrolní
    # hlášení. The first is looked up live; the second is a stored field.
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        companies = self.env["res.company"].browse({
            vals.get("company_id") or self.env.company.id for vals in vals_list})
        ignored = companies._l10n_cz_vat_status_ignored_move_ids()
        records = super().create(vals_list)
        for company in records.company_id:
            company._l10n_cz_vat_status_history_changed(
                min(records.filtered(lambda r: r.company_id == company)
                    .mapped("date_from")), ignored_before=ignored)
        return records

    def write(self, vals):
        before = {(r.company_id, r.date_from) for r in self}
        companies = self.company_id
        if vals.get("company_id"):
            companies |= self.env["res.company"].browse(vals["company_id"])
        ignored = companies._l10n_cz_vat_status_ignored_move_ids()
        res = super().write(vals)
        touched = before | {(r.company_id, r.date_from) for r in self}
        for company in {c for c, _d in touched}:
            company._l10n_cz_vat_status_history_changed(
                min(d for c, d in touched if c == company),
                ignored_before=ignored)
        return res

    def unlink(self):
        touched = {(r.company_id, r.date_from) for r in self}
        ignored = self.company_id._l10n_cz_vat_status_ignored_move_ids()
        res = super().unlink()
        for company in {c for c, _d in touched}:
            company._l10n_cz_vat_status_history_changed(
                min(d for c, d in touched if c == company),
                ignored_before=ignored)
        return res
