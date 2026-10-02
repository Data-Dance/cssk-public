# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated statutory percentages for the Slovak wage surcharges.

Like the garnishment rate table, this exists because the base module must be
installable without either payroll engine, and ``hr.rule.parameter`` belongs
to the engines. A statutory change is therefore a data change, not a code
change — which is the whole complaint about the stock Enterprise module,
where every rate is a literal inside a rule body.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .surcharge_calc import surcharge_pct


class L10nSkWageSurchargeRate(models.Model):
    _name = "l10n.sk.wage.surcharge.rate"
    _description = "Slovak Wage Surcharge Rate"
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

    # --- percentages of the MINIMUM HOURLY WAGE ---------------------------
    noc_pct = fields.Float(
        "Night work %", digits=(16, 2), default=40.0,
        help="§ 122a ods. 1 — at least 40 % of the minimum hourly wage.",
    )
    noc_risk_pct = fields.Float(
        "Night work % (risk)", digits=(16, 2), default=50.0,
        help="§ 122a ods. 2 — at least 50 % where the work is classified as "
        "risky (riziková práca).",
    )
    noc_reduced_pct = fields.Float(
        "Night work % (reduced)", digits=(16, 2), default=35.0,
        help="§ 122a ods. 3 — at least 35 %, available only by collective "
        "agreement to employers whose work is predominantly performed at "
        "night, and never for risky work.",
    )
    sobota_pct = fields.Float(
        "Saturday %", digits=(16, 2), default=50.0,
        help="§ 122b ods. 1 — at least 50 % of the minimum hourly wage.",
    )
    sobota_reduced_pct = fields.Float(
        "Saturday % (reduced)", digits=(16, 2), default=45.0,
        help="§ 122b ods. 2 — at least 45 % by collective agreement where the "
        "nature of the work requires regular work on Saturdays.",
    )
    nedela_pct = fields.Float(
        "Sunday %", digits=(16, 2), default=100.0,
        help="§ 122c ods. 1 — at least 100 % of the minimum hourly wage.",
    )
    nedela_reduced_pct = fields.Float(
        "Sunday % (reduced)", digits=(16, 2), default=90.0,
        help="§ 122c ods. 2 — at least 90 % by collective agreement where the "
        "nature of the work requires regular work on Sundays.",
    )
    stazeny_pct = fields.Float(
        "Difficult conditions %", digits=(16, 2), default=20.0,
        help="§ 123 — mzdová kompenzácia za sťažený výkon práce, at least "
        "20 % of the minimum hourly wage.",
    )
    pohotovost_pct = fields.Float(
        "Standby %", digits=(16, 2), default=20.0,
        help="§ 96 ods. 5 — at least 20 % of the minimum hourly wage for each "
        "hour of inactive standby away from the workplace.",
    )

    # --- percentages of AVERAGE EARNINGS ----------------------------------
    sviatok_pct = fields.Float(
        "Public holiday %", digits=(16, 2), default=100.0,
        help="§ 122 ods. 1 — at least 100 % of average earnings for work "
        "performed on a public holiday.",
    )
    nadcas_pct = fields.Float(
        "Overtime %", digits=(16, 2), default=25.0,
        help="§ 121 ods. 1 — at least 25 % of average earnings on top of the "
        "wage for the overtime hour itself.",
    )
    nadcas_risk_pct = fields.Float(
        "Overtime % (risk)", digits=(16, 2), default=35.0,
        help="§ 121 ods. 1 — at least 35 % where the work is classified as "
        "risky (riziková práca).",
    )
    standard_weekly_hours = fields.Float(
        "Standard weekly hours", digits=(16, 2), default=40.0, required=True,
        help="Ustanovený týždenný pracovný čas per § 85 ods. 5 ZP — the "
        "reference week the hourly minimum-wage claims are stated against. "
        "§ 120 ods. 5 raises those claims in proportion where the employer's "
        "established week is shorter. Dated here rather than hardcoded so an "
        "amendment is a data change.",
    )

    @api.depends("date_from")
    def _compute_name(self):
        for rate in self:
            rate.name = _("Wage surcharges from %(date)s", date=rate.date_from or "")

    @api.model
    def _get_rate(self, date):
        """Return the rate record in force on *date*."""
        rate = self.search([("date_from", "<=", date)], order="date_from desc", limit=1)
        if not rate:
            raise UserError(
                _(
                    "No Slovak wage-surcharge rates are configured as of "
                    "%(date)s. Add a Wage Surcharge Rate record before "
                    "computing surcharges.",
                    date=date,
                )
            )
        return rate

    def _rates_dict(self):
        """Shape the record into the plain dict the calculator expects."""
        self.ensure_one()
        return {
            "noc_pct": self.noc_pct,
            "noc_risk_pct": self.noc_risk_pct,
            "noc_reduced_pct": self.noc_reduced_pct,
            "sobota_pct": self.sobota_pct,
            "sobota_reduced_pct": self.sobota_reduced_pct,
            "nedela_pct": self.nedela_pct,
            "nedela_reduced_pct": self.nedela_reduced_pct,
            "stazeny_pct": self.stazeny_pct,
            "pohotovost_pct": self.pohotovost_pct,
            "sviatok_pct": self.sviatok_pct,
            "nadcas_pct": self.nadcas_pct,
            "nadcas_risk_pct": self.nadcas_risk_pct,
            "standard_weekly_hours": self.standard_weekly_hours,
        }

    def _pct(self, code, risk=False, reduced=False):
        """Convenience accessor used by the views and the payslip mixin."""
        self.ensure_one()
        return surcharge_pct(self._rates_dict(), code, risk=risk, reduced=reduced)
