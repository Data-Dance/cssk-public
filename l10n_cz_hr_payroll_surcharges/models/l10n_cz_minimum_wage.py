# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated Czech minimum wage (základní sazba minimální mzdy).

Kept as data rather than as an ``hr.rule.parameter`` for the same reason as
the Slovak sibling: this module must install without either payroll engine,
and rule parameters belong to the engines.

Only the BASIC rate lives here. Since 1 January 2025 (zákon č. 230/2024 Sb.)
*zaručená mzda* has been abolished for the private sector, leaving a single
minimum wage for every commercial employer regardless of the job's difficulty
— which is why this model has nothing resembling the Slovak stupne
náročnosti, and why there is no ``hr.job`` degree field in this module. The
four remaining *zaručený plat* groups apply to the public sector (plat), a
different pay regime that this module does not attempt to cover.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nCzMinimumWage(models.Model):
    _name = "l10n.cz.minimum.wage"
    _description = "Czech Minimum Wage"
    _order = "date_from desc"

    _date_uniq = models.Constraint(
        "unique(date_from)",
        "Only one minimum-wage record per start date.",
    )

    name = fields.Char(compute="_compute_name", store=True)
    date_from = fields.Date(
        required=True,
        help="First day on which this minimum wage applies.",
    )
    amount_monthly = fields.Float(
        "Monthly (Kč)", digits=(16, 2), required=True,
        help="Základní sazba minimální mzdy per month, for the stanovená "
        "týdenní pracovní doba.",
    )
    amount_hourly = fields.Float(
        "Hourly (Kč)", digits=(16, 2), required=True,
        help="Základní sazba minimální mzdy per hour, quoted for a 40-hour "
        "week. A shorter established week raises it proportionally.",
    )

    @api.depends("date_from", "amount_monthly", "amount_hourly")
    def _compute_name(self):
        for record in self:
            if not record.date_from:
                record.name = _("Czech minimum wage")
                continue
            record.name = _(
                "%(date)s — %(monthly).2f Kč / %(hourly).2f Kč per hour",
                date=record.date_from.strftime("%-d.%-m.%Y"),
                monthly=record.amount_monthly,
                hourly=record.amount_hourly,
            )

    @api.constrains("amount_monthly", "amount_hourly")
    def _check_amounts(self):
        for record in self:
            if record.amount_monthly <= 0.0 or record.amount_hourly <= 0.0:
                raise UserError(
                    _("The Czech minimum wage must be a positive amount.")
                )

    @api.model
    def _get_for_date(self, date):
        """The record in force on *date*.

        Raises rather than returning an empty recordset: every caller is about
        to compute a statutory minimum, and a missing rate would silently
        become a zero surcharge or a zero top-up.
        """
        record = self.search(
            [("date_from", "<=", date)], order="date_from desc", limit=1
        )
        if not record:
            raise UserError(
                _(
                    "No Czech minimum wage is configured for %(date)s. Add the "
                    "record under Payroll ▸ Configuration ▸ Czech Minimum Wage.",
                    date=date,
                )
            )
        return record
