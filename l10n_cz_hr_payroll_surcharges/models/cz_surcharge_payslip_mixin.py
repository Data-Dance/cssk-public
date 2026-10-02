# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The payslip half of the surcharge feature, kept engine-neutral.

An ``AbstractModel`` so the base module drags in neither engine's
``hr.payslip``; the two bridge modules mix it into their engine's payslip and
add the salary rules that call it.

Where the hours come from
-------------------------
Two sources, checked in this order for every surcharge code:

1. A **worked-days line** carrying that code — the good path, meaning real
   work entries drove the hours. Only Enterprise ships the ``hr_work_entry``
   stack, so in practice that is the ``_dd`` bridge.
2. A **payslip input** carrying that code, whose ``amount`` is read as hours.

Falling back rather than choosing lets a site migrate from hand-entered
inputs to work entries per employee, and keeps the OCA engine — which has no
work-entry stack — working at all. Where both exist the worked days win,
because they are the auditable source.
"""

from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .surcharge_calc import (
    BASE_AVG_EARNINGS,
    CODE_DIFFICULT,
    SURCHARGE_BASE,
    SURCHARGE_CODES,
    min_wage_hourly,
    min_wage_topup_hourly,
    min_wage_topup_monthly,
    surcharge_amount,
)

# Worked-day codes counting as ordinary working time — the denominator of the
# minimum-wage comparison. Overtime is deliberately absent: § 111 odst. 3
# keeps práce přesčas out of the comparison on both sides.
ORDINARY_WORK_CODES = ("WORK100",)

# Absence codes the Czech country modules put on their leave types. Only the
# OCA engine needs them subtracted — see ``_l10n_cz_work100_is_gross``.
ABSENCE_WORK_CODES = (
    "CZHOLIDAY",
    "CZSICK",
    "CZOCR",
    "CZUNPAID",
    "CZOBSTACLE",
    "CZMATERSKA",
    "CZRODICOVSKA",
    "CZOTCOVSKA",
    "CZPROSTOJ",
    "CZPOVETRNOST",
    "CZCASTECNA",
    "CZJINEPREKAZKY",
)


class CzSurchargePayslipMixin(models.AbstractModel):
    _name = "cz.surcharge.payslip.mixin"
    _description = "Czech Wage Surcharge Payslip Mixin"

    l10n_cz_surcharge_total = fields.Float(
        "Wage Surcharges",
        compute="_compute_l10n_cz_surcharge_total",
        help="Sum of every statutory wage surcharge on this payslip. Shown "
        "for reference; the individual amounts are separate payslip lines.",
    )

    def _compute_l10n_cz_surcharge_total(self):
        for slip in self:
            slip.l10n_cz_surcharge_total = sum(
                slip._l10n_cz_surcharge_amount(code) for code in SURCHARGE_CODES
            )

    # ------------------------------------------------------------------
    # engine adapters
    # ------------------------------------------------------------------
    def _l10n_cz_version(self):
        """The contract record, whatever this engine calls it.

        Enterprise names the payslip's contract ``version_id``; the OCA engine
        kept ``contract_id``. Both point at ``hr.version`` in Odoo 19.
        """
        self.ensure_one()
        if "version_id" in self._fields:
            return self.version_id
        return self.contract_id

    def _l10n_cz_avg_hourly(self):
        """Průměrný hodinový výdělek (§ 351 an.), from the country module.

        Four of the five Czech surcharges are a percentage of this, so a
        missing helper must raise rather than quietly yield zero.
        """
        self.ensure_one()
        if not hasattr(self, "l10n_cz_average_hourly_earnings"):
            raise UserError(
                _(
                    "The average-earnings helper is missing. Install one of "
                    "the Czech payroll modules (l10n_cz_hr_payroll_oca or "
                    "l10n_cz_hr_payroll_ee) — overtime, public holiday, night "
                    "and weekend surcharges are percentages of average "
                    "earnings and cannot be computed without it."
                )
            )
        return self.l10n_cz_average_hourly_earnings()

    # ------------------------------------------------------------------
    # rates
    # ------------------------------------------------------------------
    def _l10n_cz_rate_record(self):
        self.ensure_one()
        return self.env["l10n.cz.wage.surcharge.rate"]._get_for_date(self.date_from)

    def _l10n_cz_minimum_wage_record(self):
        self.ensure_one()
        return self.env["l10n.cz.minimum.wage"]._get_for_date(self.date_from)

    def _l10n_cz_min_wage_hourly(self):
        """The hourly minimum-wage claim, adjusted for a shorter week."""
        self.ensure_one()
        wage = self._l10n_cz_minimum_wage_record()
        rate = self._l10n_cz_rate_record()
        calendar = (
            self._l10n_cz_version().resource_calendar_id
            or self.company_id.resource_calendar_id
        )
        return min_wage_hourly(
            wage.amount_hourly,
            calendar.hours_per_week if calendar else 0.0,
            rate.standard_weekly_hours,
        )

    def _l10n_cz_hourly_base(self, code):
        """The hourly amount *code* is a percentage of."""
        self.ensure_one()
        if SURCHARGE_BASE[code] == BASE_AVG_EARNINGS:
            return self._l10n_cz_avg_hourly()
        return self._l10n_cz_min_wage_hourly()

    # ------------------------------------------------------------------
    # hours
    # ------------------------------------------------------------------
    def _l10n_cz_surcharge_hours(self, code):
        """Hours attracting the surcharge *code*, worked days before inputs."""
        self.ensure_one()
        hours = sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code == code
        )
        if hours:
            return hours
        return sum(
            abs(line.amount) for line in self.input_line_ids if line.code == code
        )

    def _l10n_cz_difficult_factors(self):
        """How many § 117 aggravating influences apply to this contract.

        Each earns its own 10 %, so this is a multiplier rather than a flag.
        Zero means the surcharge does not apply at all, which is why hours
        alone cannot drive it.
        """
        self.ensure_one()
        return self._l10n_cz_version().l10n_cz_difficult_factors or 0

    def _l10n_cz_surcharge_amount(self, code):
        """Money owed for surcharge *code* on this payslip."""
        self.ensure_one()
        hours = self._l10n_cz_surcharge_hours(code)
        if not hours:
            return 0.0
        version = self._l10n_cz_version()
        agreed = bool(version.l10n_cz_surcharge_agreed)
        rate = self._l10n_cz_rate_record()
        factors = (
            self._l10n_cz_difficult_factors() if code == CODE_DIFFICULT else 1
        )
        return surcharge_amount(
            hours,
            self._l10n_cz_hourly_base(code),
            rate.percentage_for(code, agreed=agreed),
            factors=factors,
        )

    # ------------------------------------------------------------------
    # ordinary working time, for the minimum-wage comparison
    # ------------------------------------------------------------------
    def _l10n_cz_work100_is_gross(self):
        """Whether the ordinary-work line still contains absence hours.

        The engines disagree and getting it wrong silently overpays. The OCA
        engine's ``_compute_worked_days`` returns the FULL days the calendar
        schedules and puts absences on separate lines; Enterprise groups real
        work entries by type, so an absence never lands in ``WORK100`` at all.
        The ``_oca`` bridge overrides this.
        """
        return False

    def _l10n_cz_absence_hours(self):
        self.ensure_one()
        return sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code in ABSENCE_WORK_CODES
        )

    def _l10n_cz_ordinary_hours(self):
        """Hours actually worked in ordinary working time.

        Net of absences, because the comparison pairs these hours with the
        wage actually paid: an employee absent all month has their basic wage
        prorated to zero, and pairing that zero with a full month of hours
        would claim the whole monthly minimum wage as a top-up for someone who
        did not work.

        Falls back to the period's scheduled hours only when there are no
        worked-days lines at all. Both engines have that state — the OCA
        engine builds worked days from an onchange, Enterprise skips them
        under ``salary_simulation`` — and in it both pay the full monthly
        wage, so the full month's hours are the right partner. The test is on
        the PRESENCE of lines, not on the hours being non-zero: a full month
        of absence legitimately yields zero hours, and falling back there
        would resurrect the bug above.
        """
        self.ensure_one()
        if not self.worked_days_line_ids:
            return self._l10n_cz_scheduled_hours()
        hours = sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code in ORDINARY_WORK_CODES
        )
        if self._l10n_cz_work100_is_gross():
            hours -= self._l10n_cz_absence_hours()
        return max(0.0, hours)

    def _l10n_cz_calendar_hours(self, calendar):
        self.ensure_one()
        if not calendar:
            return 0.0
        data = self.employee_id._get_work_days_data_batch(
            datetime.combine(self.date_from, time.min),
            datetime.combine(self.date_to, time.max),
            calendar=calendar,
            compute_leaves=False,
        )
        return data.get(self.employee_id.id, {}).get("hours", 0.0)

    def _l10n_cz_scheduled_hours(self):
        self.ensure_one()
        return self._l10n_cz_calendar_hours(
            self._l10n_cz_version().resource_calendar_id
        )

    def _l10n_cz_full_time_hours(self):
        """Hours a FULL-TIME contract would schedule in the same period.

        Deliberately not the employee's own schedule: prorating a part-timer
        against their own calendar always gives a ratio of 1 and would hold
        them to the undiminished monthly minimum, which is backwards.
        """
        self.ensure_one()
        return self._l10n_cz_calendar_hours(
            self.company_id.resource_calendar_id
        ) or self._l10n_cz_scheduled_hours()

    # ------------------------------------------------------------------
    # doplatek do minimální mzdy (§ 111 odst. 3)
    # ------------------------------------------------------------------
    def _l10n_cz_min_wage_topup(self, qualifying_wage, hourly_paid=False):
        """Top-up owed so the qualifying wage reaches the minimum.

        *qualifying_wage* must already exclude overtime pay and every
        surcharge this module computes — § 111 odst. 3 keeps them out, so that
        a night shift cannot paper over a sub-minimum base wage. The engine
        bridges are responsible for handing in the right figure; doing the
        exclusion here would mean guessing at rule codes that differ per
        engine.
        """
        self.ensure_one()
        hours = self._l10n_cz_ordinary_hours()
        if hourly_paid:
            return min_wage_topup_hourly(
                qualifying_wage, hours, self._l10n_cz_min_wage_hourly()
            )
        return min_wage_topup_monthly(
            qualifying_wage,
            hours,
            self._l10n_cz_full_time_hours(),
            self._l10n_cz_minimum_wage_record().amount_monthly,
        )
