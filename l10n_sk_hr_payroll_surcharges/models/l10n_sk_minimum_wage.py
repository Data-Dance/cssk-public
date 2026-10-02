# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Minimálne mzdové nároky — the six stupne náročnosti práce (§ 120 ZP).

§ 120 ods. 4 derives each level from the base monthly minimum wage and a
coefficient (1.0 / 1.2 / 1.4 / 1.6 / 1.8 / 2.0) anchored on the 2020 figure of
€580. The derived amounts are published every year, and the published table is
what payroll practice actually uses, so the table is shipped as data rather
than recomputed: re-deriving it would only add a rounding argument nobody
needs, and a future amendment to the formula would silently produce numbers
that match no official table.

The base (level 1) hourly figure is also the ``minimálna mzda v eurách za
hodinu`` that the night / Saturday / Sunday / difficult-work / standby
surcharges are percentages of.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

LEVEL_SELECTION = [
    ("1", "1 — pomocné práce"),
    ("2", "2 — jednoduché odborné práce"),
    ("3", "3 — odborné práce"),
    ("4", "4 — zložité odborné práce"),
    ("5", "5 — veľmi zložité odborné práce"),
    ("6", "6 — vysoko špecializované práce"),
]


class L10nSkMinimumWage(models.Model):
    _name = "l10n.sk.minimum.wage"
    _description = "Slovak Minimum Wage Claim (stupeň náročnosti)"
    _order = "date_from desc, level"

    _date_level_uniq = models.Constraint(
        "unique(date_from, level)",
        "Only one minimum-wage claim per start date and difficulty level.",
    )

    name = fields.Char(compute="_compute_name", store=True)
    date_from = fields.Date(
        required=True,
        help="First day on which this claim applies. The Slovak minimum wage "
        "changes on 1 January.",
    )
    level = fields.Selection(
        LEVEL_SELECTION,
        required=True,
        string="Stupeň náročnosti",
        help="Difficulty level of the job per § 120 ods. 2 and the Annex 1 to "
        "the Zákonník práce.",
    )
    amount_monthly = fields.Float(
        "Monthly claim", digits=(16, 2), required=True,
        help="Minimálny mzdový nárok for a monthly-paid employee (EUR).",
    )
    amount_hourly = fields.Float(
        "Hourly claim", digits=(16, 3), required=True,
        help="Minimálny mzdový nárok per hour at a 40-hour week (EUR). "
        "A shorter established weekly working time raises it proportionally "
        "(§ 120 ods. 5).",
    )

    @api.depends("date_from", "level")
    def _compute_name(self):
        for record in self:
            record.name = _(
                "Level %(level)s from %(date)s",
                level=record.level or "",
                date=record.date_from or "",
            )

    @api.model
    def _get_claim(self, date, level="1"):
        """Return the claim record for *level* in force on *date*."""
        claim = self.search(
            [("date_from", "<=", date), ("level", "=", str(level))],
            order="date_from desc",
            limit=1,
        )
        if not claim:
            raise UserError(
                _(
                    "No Slovak minimum-wage claim is configured for level "
                    "%(level)s as of %(date)s. Add a Minimum Wage record "
                    "before computing payslips.",
                    level=level,
                    date=date,
                )
            )
        return claim

    @api.model
    def _get_base_hourly(self, date):
        """The level-1 hourly minimum wage the surcharges are a % of."""
        return self._get_claim(date, "1").amount_hourly
