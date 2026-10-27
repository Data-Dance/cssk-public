# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math
from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta
from pytz import timezone

from odoo import _, models
from odoo.addons.l10n_cz_hr_payroll_base.models.health_calc import (
    health_premiums,
)

# Stable Czech payroll worked-day codes for the absence taxonomy. Every one of
# these is an ABSENCE: it prorates BASIC down. Holiday / paid-obstacle time is
# then compensated back at the průměrný výdělek by dedicated náhrada rules;
# sickness by SICKNAHRADA; OČR and unpaid leave get no employer pay.
# § 207-209 obstacles on the EMPLOYER's side, each with its own statutory
# náhrada rate (80 / 60 / 100 / 60 % of průměrný výdělek). They cannot share
# one bucket the way the § 199 employee-side reasons do: the worked-day line is
# keyed by code, so a single bucket would lose the rate and pay them all in
# full.
CZ_EMPLOYER_OBSTACLE_CODES = (
    "CZPROSTOJ",
    "CZPOVETRNOST",
    "CZJINEPREKAZKY",
    "CZCASTECNA",
)

# Mateřská (§ 195) / rodičovská (§ 196) / otcovská. The employer pays NOTHING
# — peněžitá pomoc v mateřství, rodičovský příspěvek and otcovská are dávky of
# ČSSZ — so they behave like OČR: they cut worked time and get no náhrada.
# Separate codes rather than folded into OČR because the ČSSZ filings must tell
# them apart, and the vyloučené doby on the ELDP differ.
CZ_FAMILY_LEAVE_CODES = ("CZMATERSKA", "CZRODICOVSKA", "CZOTCOVSKA")

CZ_ABSENCE_CODES = (
    "CZHOLIDAY", "CZSICK", "CZOCR", "CZUNPAID", "CZOBSTACLE",
) + CZ_EMPLOYER_OBSTACLE_CODES + CZ_FAMILY_LEAVE_CODES


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _l10n_cz_version(self):
        """The contract (``hr.version``) the payslip is computed on.

        OCA payroll fills ``contract_id`` only in the form's onchange and in
        the batch wizard; a payslip created through the API leaves it empty
        while ``compute_sheet`` still resolves the employee's contract for the
        rules. Fall back to that same resolution so the helpers below see the
        contract the rules see.
        """
        self.ensure_one()
        return self.contract_id or self._get_employee_contracts()[:1]

    def rule_parameter(self, code):
        """Accessor for dated statutory parameters.

        Returns the value of the ``hr.rule.parameter`` with ``code`` that is
        effective at the payslip ``date_to``.
        """
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_value(code, self.date_to)

    # -- Absence -> worked-day lines --------------------------------------

    def _compute_leave_days(self, contract, day_from, day_to):
        """Key each leave worked-day line by the leave type's Czech payroll code.

        The OCA base keys leave lines by ``holiday_status_id`` (name) and falls
        back to the ``GLOBAL`` code because the OCA stack has no
        ``hr.work.entry.type``. We instead re-key by the stable
        ``l10n_cz_payroll_code`` on the leave type so the salary rules can read
        absence hours per code (CZHOLIDAY / CZSICK / …). These codes map 1:1 onto
        Odoo master's unified Time Type ``code``
        (see docs/master_work_entry_analysis.md).
        """
        leaves_positive = (
            self.env["ir.config_parameter"].sudo().get_param("payroll.leaves_positive")
        )
        leaves = {}
        calendar = contract.resource_calendar_id
        tz = timezone(calendar.tz or contract.employee_id.tz or "UTC")
        day_leave_intervals = contract.employee_id.list_leaves(
            day_from, day_to, calendar=contract.resource_calendar_id
        )
        for day, hours, leave in day_leave_intervals:
            holiday = leave[:1].holiday_id
            leave_type = holiday.holiday_status_id
            code = (
                leave_type.l10n_cz_payroll_code
                # Cross-install: an SK leave type carries its own code; key it
                # correctly even when this CZ override wins the hr.payslip MRO.
                or getattr(leave_type, "l10n_sk_payroll_code", False)
                or getattr(
                    getattr(leave_type, "work_entry_type_id", None), "code", None
                )
                or "GLOBAL"
            )
            current_leave_struct = leaves.setdefault(
                code,
                {
                    "name": leave_type.name or _("Global Leaves"),
                    "sequence": 5,
                    "code": code,
                    "number_of_days": 0.0,
                    "number_of_hours": 0.0,
                    "contract_id": contract.id,
                },
            )
            if leaves_positive:
                current_leave_struct["number_of_hours"] += hours
            else:
                current_leave_struct["number_of_hours"] -= hours
            work_hours = calendar.get_work_hours_count(
                tz.localize(datetime.combine(day, time.min)),
                tz.localize(datetime.combine(day, time.max)),
                compute_leaves=False,
            )
            if work_hours:
                if leaves_positive:
                    current_leave_struct["number_of_days"] += hours / work_hours
                else:
                    current_leave_struct["number_of_days"] -= hours / work_hours
        return leaves.values()

    def l10n_cz_leave_hours(self, codes):
        """Sum absence hours (always positive) of the given worked-day code(s)."""
        self.ensure_one()
        if isinstance(codes, str):
            codes = (codes,)
        return sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code in codes
        )

    def l10n_cz_worked_ratio(self):
        """Fraction of the period's scheduled time paid as BASIC wage.

        Returns 1.0 for a full worked month and < 1.0 for a mid-month
        hire/leaver OR when an absence (holiday, sickness, OČR, unpaid, paid
        obstacle) reduces the worked time. The WORK100 line carries the full
        scheduled hours of the contract-active part of the period (leaves are
        NOT subtracted by the OCA engine), so we subtract the absence hours here
        and divide by the full-period scheduled hours.
        """
        self.ensure_one()
        contract = self._l10n_cz_version()
        calendar = contract.resource_calendar_id
        if not calendar:
            return 1.0
        day_from = datetime.combine(self.date_from, time.min)
        day_to = datetime.combine(self.date_to, time.max)
        scheduled = contract.employee_id._get_work_days_data_batch(
            day_from, day_to, calendar=calendar, compute_leaves=False,
        )[contract.employee_id.id]["hours"]
        if not scheduled:
            return 1.0
        worked = self.worked_days_line_ids.filtered(lambda w: w.code == "WORK100")
        if not worked:
            # Directly-created payslip with no worked-day detail -> full month.
            return 1.0
        worked_hours = sum(worked.mapped("number_of_hours"))
        absence = self.l10n_cz_leave_hours(CZ_ABSENCE_CODES)
        return min(max(worked_hours - absence, 0.0) / scheduled, 1.0)

    def l10n_cz_sick_compensated_hours(self):
        """CZSICK hours the employer compensates (§ 192 odst. 1 zákoníku práce).

        Náhrada mzdy covers only the first 14 calendar days of an
        uninterrupted dočasná pracovní neschopnost; from day 15 the employee
        is paid nemocenské by ČSSZ. The hours past that point are traced back
        to their time-off request and taken off.
        """
        self.ensure_one()
        hours = self.l10n_cz_leave_hours("CZSICK")
        if not hours:
            return 0.0
        calendar = (
            self._l10n_cz_version().resource_calendar_id
            or self.employee_id.resource_calendar_id
        )
        excess = self.employee_id._l10n_cz_sick_hours_after_employer_period(
            self.date_from,
            self.date_to,
            calendar,
            lambda leave_type: leave_type.l10n_cz_payroll_code == "CZSICK",
        )
        return max(hours - excess, 0.0)

    def l10n_cz_health_premiums(self, base):
        """Employee and employer health premium for this payslip.

        Returns ``(employee, employer)``, both positive whole crowns: the
        13,5 % premium rounded up per employee (§ 2 odst. 2 zák. 592/1992),
        split one third / two thirds with the employee's third rounded up
        (§ 9 odst. 2 zák. 48/1997), at least from the minimum base prorated by
        calendar days (§ 3 odst. 9 zák. 592/1992). The minimum base applies to
        standard employment only, and not to a state-insured person or a
        ZTP/P holder (§ 3 odst. 8 písm. a) and d)). When an employer-side
        obstacle (§§ 207-209 ZP) is on the payslip the employer pays the
        top-up (§ 3 odst. 10, last sentence).
        """
        self.ensure_one()
        version = self._l10n_cz_version()
        min_base = 0.0
        if (
            version.l10n_cz_agreement_type == "standard"
            and not version.l10n_cz_is_state_insured
            and not version.l10n_cz_claim_ztpp
        ):
            min_base = self.rule_parameter(
                "l10n_cz_health_min_base"
            ) * version._l10n_cz_health_min_base_ratio(
                self.date_from,
                self.date_to,
                lambda leave_type: leave_type.l10n_cz_payroll_code,
            )
        return health_premiums(
            base,
            min_base,
            self.rule_parameter("l10n_cz_health_rate_ee"),
            self.rule_parameter("l10n_cz_health_rate_er"),
            employer_pays_topup=self.l10n_cz_leave_hours(
                CZ_EMPLOYER_OBSTACLE_CODES
            ) > 0,
        )

    def _l10n_cz_discount_hours(self):
        """Hours counted for the § 7a odst. 3 písm. b) and c) zák. 589/1992 tests.

        Hours worked, overtime included, plus every hour paid by a náhrada
        mzdy (dovolená, obstacles, the employer's part of a sickness): the
        statute counts "též hodina, za kterou ... náleží náhrada mzdy". With
        no worked-day lines at all, the contract's scheduled hours.
        """
        self.ensure_one()
        version = self._l10n_cz_version()
        if not self.worked_days_line_ids:
            calendar = (version.resource_calendar_id
                        or self.employee_id.resource_calendar_id)
            if not calendar:
                return 0.0
            return self.employee_id._get_work_days_data_batch(
                datetime.combine(self.date_from, time.min),
                datetime.combine(self.date_to, time.max),
                calendar=calendar,
                compute_leaves=False,
            )[self.employee_id.id]["hours"]
        # The OCA engine's WORK100 still contains the absences.
        work = max(
            sum(
                abs(line.number_of_hours)
                for line in self.worked_days_line_ids
                if line.code == "WORK100"
            ) - self.l10n_cz_leave_hours(CZ_ABSENCE_CODES),
            0.0,
        )
        overtime = self.l10n_cz_leave_hours("PRESCAS") or sum(
            abs(line.amount)
            for line in self.input_line_ids
            if line.code == "PRESCAS"
        )
        paid_absence = self.l10n_cz_leave_hours(
            ("CZHOLIDAY", "CZOBSTACLE") + CZ_EMPLOYER_OBSTACLE_CODES
        ) + self.l10n_cz_sick_compensated_hours()
        if not self.l10n_cz_leave_hours("CZSICK"):
            # The sickness compensation rule falls back to this input too.
            paid_absence += sum(
                abs(line.amount)
                for line in self.input_line_ids
                if line.code == "SICK_HOURS"
            )
        return work + overtime + paid_absence

    def l10n_cz_social_discount_eligible(self, base):
        """Whether the employer may claim the sleva na pojistném (§ 7a zák. 589/1992).

        Checks what the payslip can see; the notification to ČSSZ (odst. 5),
        the one-employer rule (odst. 4) and the eligibility reason itself are
        the user's to vouch for through the category on the contract.

        * pracovní poměr only (odst. 1) — never a dohoda;
        * categories a)-f): an agreed shorter working time of 8-30 h a week
          (odst. 2) and at most 138 hours in the month, prorated for a partial
          month of employment and rounded up (odst. 3 písm. c));
        * the monthly base at most 1,5 × the average wage (odst. 3 písm. a));
        * the base per hour, rounded up, at most 1,15 % of the average wage,
          rounded up (odst. 3 písm. b)).
        """
        self.ensure_one()
        version = self._l10n_cz_version()
        category = version.l10n_cz_social_discount_category
        if not category or category == "none":
            return False
        if version.l10n_cz_agreement_type != "standard":
            return False
        if base <= 0.0:
            return False
        avg_wage = self.rule_parameter("l10n_cz_avg_wage")
        if base > math.ceil(round(
            avg_wage * self.rule_parameter("l10n_cz_social_disc_base_mult"), 6)):
            return False
        hours = self._l10n_cz_discount_hours()
        if hours <= 0.0:
            return False
        hourly_cap = math.ceil(
            round(avg_wage * self.rule_parameter("l10n_cz_social_disc_hourly_pct") / 100.0, 6)
        )
        if math.ceil(round(base / hours, 6)) > hourly_cap:
            return False
        if category == "under21":
            return True
        calendar = version.resource_calendar_id
        if not calendar:
            return False
        if "hours_per_week" in calendar._fields:
            weekly = calendar.hours_per_week
        else:
            weeks = 2.0 if calendar.two_weeks_calendar else 1.0
            weekly = sum(
                a.hour_to - a.hour_from for a in calendar.attendance_ids
            ) / weeks
        if not (
            self.rule_parameter("l10n_cz_social_disc_hours_min")
            <= weekly
            <= self.rule_parameter("l10n_cz_social_disc_hours_max")
        ):
            return False
        period_days = (self.date_to - self.date_from).days + 1
        start = max(self.date_from, version.contract_date_start or self.date_from)
        end = min(self.date_to, version.contract_date_end or self.date_to)
        employed_days = max((end - start).days + 1, 0)
        month_cap = math.ceil(round(
            self.rule_parameter("l10n_cz_social_disc_hours_month_max")
            * employed_days / period_days, 6))
        return hours <= month_cap

    # -- Average earnings (průměrný výdělek, §351-362 zákoníku práce) -------

    def _l10n_cz_previous_quarter(self):
        """Rozhodné období = the calendar quarter preceding date_from (§354)."""
        self.ensure_one()
        d = self.date_from
        cur_q_start = date(d.year, ((d.month - 1) // 3) * 3 + 1, 1)
        prev_q_end = cur_q_start - relativedelta(days=1)
        prev_q_start = date(
            prev_q_end.year, ((prev_q_end.month - 1) // 3) * 3 + 1, 1
        )
        return prev_q_start, prev_q_end

    def _l10n_cz_probable_hourly(self):
        """Pravděpodobný výdělek (§355): monthly wage / scheduled monthly hours.

        Used when the employee has no usable prior-quarter earnings.
        Simplification: derived from the current contract wage and the period's
        scheduled hours rather than the earnings achieved so far in the quarter.
        """
        self.ensure_one()
        contract = self._l10n_cz_version()
        # Fall back to the employee's own calendar. A version without one
        # would otherwise return 0.0 here, floor to the minimum wage and
        # pay every náhrada at that. The Enterprise engine has always had
        # this fallback; the two differed only in how tolerant they were.
        calendar = (contract.resource_calendar_id
                    or self.employee_id.resource_calendar_id)
        if not calendar:
            return 0.0
        day_from = datetime.combine(self.date_from, time.min)
        day_to = datetime.combine(self.date_to, time.max)
        scheduled = contract.employee_id._get_work_days_data_batch(
            day_from, day_to, calendar=calendar, compute_leaves=False,
        )[contract.employee_id.id]["hours"]
        return contract.wage / scheduled if scheduled else 0.0

    def l10n_cz_average_hourly_earnings(self):
        """Průměrný hodinový výdělek (PHV), §351-362 zákoníku práce.

        rozhodné období = the previous calendar quarter; PHV = counted gross
        earnings in that quarter / hours worked in that quarter. The manual
        ``l10n_cz_avg_hourly_earnings`` field, if set, is used as an override.
        Otherwise the PHV is computed from the employee's prior-quarter payslips
        (counted gross = the BASIC worked-time wage, which per §356 excludes
        náhrady mzdy; worked hours = WORK100 minus absences). When there is no
        usable prior quarter, pravděpodobný výdělek is used (§355). The result is
        floored at the minimum-wage hourly rate (§357).

        Sources: §351-362 zákona 262/2006 Sb.; MPSV metodika XXI (příručka).
        Simplifications: counted gross approximated by BASIC; the "21 worked
        days" test approximated by "any worked hours in the quarter".
        """
        self.ensure_one()
        contract = self._l10n_cz_version()
        min_hourly = self.rule_parameter("l10n_cz_min_wage_hourly")
        manual = contract.l10n_cz_avg_hourly_earnings
        if manual:
            return max(manual, min_hourly)
        q_start, q_end = self._l10n_cz_previous_quarter()
        prior = self.search([
            ("employee_id", "=", self.employee_id.id),
            ("state", "=", "done"),
            ("date_from", ">=", q_start),
            ("date_to", "<=", q_end),
        ])
        counted = sum(p.get_salary_line_total("BASIC") for p in prior)
        hours = 0.0
        for p in prior:
            work = sum(
                p.worked_days_line_ids.filtered(
                    lambda w: w.code == "WORK100"
                ).mapped("number_of_hours")
            )
            hours += max(work - p.l10n_cz_leave_hours(CZ_ABSENCE_CODES), 0.0)
        if hours >= 1.0 and counted > 0:
            phv = counted / hours
        else:
            phv = self._l10n_cz_probable_hourly()
        return max(phv, min_hourly)

    def _get_baselocaldict(self, contracts):
        # The payroll engine only injects ``math`` (via tools) into the
        # salary-rule namespace.  The Czech income-tax and cap rules need date
        # helpers, so we also expose ``relativedelta``.
        localdict = super()._get_baselocaldict(contracts)
        localdict["relativedelta"] = relativedelta
        return localdict
