# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated statutory percentages for the Czech wage surcharges.

Data rather than code, so that a statutory change is a data change — the same
complaint about the stock Enterprise payroll modules, where every rate is a
literal inside a rule body.

Every percentage here is a MINIMUM ("nejméně"). An employer who pays more
should raise the figure here, or add a record dated from the agreement, rather
than patch the salary rules.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .surcharge_calc import (
    SURCHARGE_BASE,
    SURCHARGE_CODES,
    SUPPORTS_AGREED,
    surcharge_pct,
)


class L10nCzWageSurchargeRate(models.Model):
    _name = "l10n.cz.wage.surcharge.rate"
    _description = "Czech Wage Surcharge Rate"
    _order = "date_from desc"

    _date_uniq = models.Constraint(
        "unique(date_from)",
        "Only one wage-surcharge rate record per start date.",
    )

    name = fields.Char(compute="_compute_name", store=True)
    date_from = fields.Date(
        required=True,
        help="First day on which these percentages apply.",
    )

    # --- percentages of AVERAGE EARNINGS (průměrný výdělek, § 351 an.) ----
    prescas_pct = fields.Float(
        "Overtime %", digits=(16, 2), default=25.0,
        help="§ 114 odst. 1 — at least 25 % of average earnings, unless "
        "compensatory time off (náhradní volno) is agreed instead.",
    )
    svatek_pct = fields.Float(
        "Public holiday %", digits=(16, 2), default=100.0,
        help="§ 115 odst. 2 — where a supplement is agreed instead of "
        "compensatory time off, at least 100 % of average earnings.",
    )
    nocni_pct = fields.Float(
        "Night work %", digits=(16, 2), default=10.0,
        help="§ 116 — at least 10 % of average earnings.",
    )
    nocni_agreed_pct = fields.Float(
        "Night work % (agreed)", digits=(16, 2),
        help="§ 116 second sentence — a different minimum amount and method "
        "of determination may be agreed. Left empty unless such an agreement "
        "exists; the statutory figure then applies.",
    )
    vikend_pct = fields.Float(
        "Saturday/Sunday %", digits=(16, 2), default=10.0,
        help="§ 118 — at least 10 % of average earnings. One rate covers both "
        "days, unlike Slovakia where § 122b and § 122c differ.",
    )
    vikend_agreed_pct = fields.Float(
        "Saturday/Sunday % (agreed)", digits=(16, 2),
        help="§ 118 second sentence — a different minimum may be agreed.",
    )

    # --- percentage of the MINIMUM WAGE ----------------------------------
    ztizene_pct = fields.Float(
        "Difficult environment %", digits=(16, 2), default=10.0,
        help="§ 117 — at least 10 % of the BASIC MINIMUM WAGE RATE (not of "
        "average earnings), for each aggravating influence listed in "
        "nařízení vlády č. 567/2006 Sb.",
    )

    standard_weekly_hours = fields.Float(
        "Standard weekly hours", digits=(16, 2), default=40.0,
        help="§ 79 odst. 1 stanovená týdenní pracovní doba, which the hourly "
        "minimum wage is quoted at.",
    )

    @api.depends("date_from")
    def _compute_name(self):
        for record in self:
            record.name = (
                record.date_from.strftime("%-d.%-m.%Y")
                if record.date_from
                else _("Czech wage surcharge rate")
            )

    @api.constrains(*["%s_pct" % code.lower() for code in SURCHARGE_CODES])
    def _check_percentages(self):
        for record in self:
            for code in SURCHARGE_CODES:
                if record["%s_pct" % code.lower()] <= 0.0:
                    raise UserError(
                        _(
                            "Every statutory surcharge percentage must be "
                            "above zero — %s is a legal minimum, not an "
                            "optional benefit.",
                            code,
                        )
                    )

    def _rates_dict(self):
        """The plain dict the Odoo-free kernel expects."""
        self.ensure_one()
        rates = {}
        for code in SURCHARGE_CODES:
            key = code.lower()
            rates["%s_pct" % key] = self["%s_pct" % key]
            if code in SUPPORTS_AGREED:
                rates["%s_agreed_pct" % key] = self["%s_agreed_pct" % key]
        return rates

    def percentage_for(self, code, agreed=False):
        """Percentage for *code* on this record."""
        self.ensure_one()
        return surcharge_pct(self._rates_dict(), code, agreed=agreed)

    def base_for(self, code):
        """Which hourly base *code* is a percentage of."""
        return SURCHARGE_BASE[code]

    @api.model
    def _get_for_date(self, date):
        """The record in force on *date*; raises if none, as for the wage."""
        record = self.search(
            [("date_from", "<=", date)], order="date_from desc", limit=1
        )
        if not record:
            raise UserError(
                _(
                    "No Czech wage-surcharge rates are configured for "
                    "%(date)s. Add the record under Payroll ▸ Configuration ▸ "
                    "Czech Wage Surcharges.",
                    date=date,
                )
            )
        return record
