# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar as _calendar
from datetime import date, datetime, time

from dateutil.relativedelta import relativedelta

from odoo import _, models

# § 142 obstacles on the EMPLOYER's side, each paid at its own statutory
# percentage of average earnings (100 / 50 / 100 / 60). They cannot share one
# bucket the way the § 141 employee-side reasons do: the worked-day line is
# keyed by code, so a single bucket would lose the rate and pay everything at
# 100 % — which is what happened before these existed.
L10N_SK_EMPLOYER_OBSTACLE_CODES = (
    "PREKAZKA_PRESTOJ",
    "PREKAZKA_POCASIE",
    "PREKAZKA_INE",
    "PREKAZKA_VAZNE",
)

# Materská / rodičovská / otcovská dovolenka (§ 166). The employer pays
# NOTHING for these — materské, rodičovský príspevok and otcovské are dávky of
# the Sociálna poisťovňa — so they behave like OČR: they cut worked days and
# get no náhrada. They are separate codes rather than folded into OČR because
# the SP filings must tell them apart: rodičovská drives a prerušenie
# povinného poistenia on the RLFO, and the vylúčené doby on the ELDP differ.
L10N_SK_FAMILY_LEAVE_CODES = ("MATERSKA", "RODICOVSKA", "OTCOVSKA")

# Leave-type payroll codes that COUNT AS AN ABSENCE (they cut worked days, so
# the basic wage is prorated down for them). Holiday / paid obstacle are added
# back as náhrada at priemerný zárobok by their own rules; PN drives the
# employer sick-pay náhrada; family care / unpaid leave / family leave are
# simply unpaid by the employer.
L10N_SK_ABSENCE_CODES = (
    "DOVOLENKA", "PN", "OCR", "NEPLATENE", "OBSTACLE",
) + L10N_SK_EMPLOYER_OBSTACLE_CODES + L10N_SK_FAMILY_LEAVE_CODES


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def l10n_sk_absence_codes(self):
        """The worked-day codes that count as an absence, for the BASIC rule.

        Exposed as a method so the rule body can read the list instead of
        carrying its own copy: it used to be duplicated in the XML, which meant
        adding an absence type in one place and forgetting the other silently
        stopped prorating the wage for it.
        """
        return L10N_SK_ABSENCE_CODES

    def rule_parameter(self, code):
        """Accessor for dated statutory parameters.

        Returns the value of the ``hr.rule.parameter`` with ``code`` that is
        effective at the payslip ``date_to``.
        """
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_value(code, self.date_to)

    # ------------------------------------------------------------------
    # Absence -> payroll code mapping
    # ------------------------------------------------------------------
    def _compute_leave_days(self, contract, day_from, day_to):
        """Key each leave worked-day line by its Slovak payroll code.

        The upstream OCA engine keys the per-leave-type worked-day line on
        ``holiday_status_id.work_entry_type_id.code`` (defaulting to ``GLOBAL``
        when the optional ``hr_work_entry`` stack is absent, as it is here).
        We instead key it on ``hr.leave.type.l10n_sk_payroll_code`` so the
        Slovak rules can tell holiday / PN / OČR / unpaid / obstacle apart
        without depending on the work-entry stack. Reimplemented from
        ``payroll/models/hr_payslip.py:_compute_leave_days`` (OCA 18.0); only
        the ``code``/``sequence`` source is changed.
        """
        from pytz import timezone

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
            # Cross-install: a CZ leave type carries its own code; key it
            # correctly even when this SK override wins the hr.payslip MRO.
            sk_code = leave_type.l10n_sk_payroll_code or getattr(
                leave_type, "l10n_cz_payroll_code", False
            )
            current_leave_struct = leaves.setdefault(
                leave_type,
                {
                    "name": leave_type.name or _("Global Leaves"),
                    "sequence": 5,
                    "code": sk_code or "GLOBAL",
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

    # ------------------------------------------------------------------
    # Average earnings (priemerný zárobok, §134 Zákonníka práce)
    # ------------------------------------------------------------------
    def _l10n_sk_previous_quarter(self):
        """Rozhodujúce obdobie = the calendar quarter BEFORE the payslip's."""
        self.ensure_one()
        d = self.date_from
        q_index = (d.month - 1) // 3  # 0..3
        year, pq = d.year, q_index - 1
        if pq < 0:
            pq, year = 3, year - 1
        start_month = pq * 3 + 1
        end_month = start_month + 2
        q_start = date(year, start_month, 1)
        q_end = date(year, end_month, _calendar.monthrange(year, end_month)[1])
        return q_start, q_end

    def l10n_sk_average_hourly_earnings(self):
        """Priemerný hodinový zárobok per §134 Zákonníka práce (č. 311/2001).

        Rozhodujúce obdobie = the previous calendar quarter. The average hourly
        earnings = gross wage credited in that quarter (EXCLUDING wage
        replacements / náhrady) ÷ hours worked in that quarter, rounded to 4
        decimals. If the employee did not work at least 168 hours in the
        determining period (§134 ods. 3) the probable earnings (pravdepodobný
        zárobok) are used instead — here the current contract wage over the
        month's scheduled hours. Finally the statutory floor applies: if the
        result is below the hourly minimum wage it is raised to it (§134 ods. 5).

        Sources: podnikajte.sk "Priemerný zárobok (dovolenkový priemer)"
        <https://www.podnikajte.sk/zamestnanci-a-hr/priemerny-zarobok-dovolenkovy-priemer>,
        Národný inšpektorát práce <https://www.ip.gov.sk/faq/104739/>,
        §134 zákona č. 311/2001 Z. z. (Zákonník práce).

        SIMPLIFICATIONS: (a) the "counted gross" is the GROSS line less the SK
        náhrada lines rather than a from-scratch §118 wage classification; (b)
        the ≥21-days alternative to the ≥168-hours test is not modelled.
        """
        self.ensure_one()
        min_hourly = self.rule_parameter("l10n_sk_min_hourly_wage")
        q_start, q_end = self._l10n_sk_previous_quarter()
        slips = self.env["hr.payslip"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date_from", ">=", q_start),
                ("date_to", "<=", q_end),
                # Only a CONFIRMED payslip counts. §134 keys on the wage
                # "zúčtovaná" in the determining period, and a payslip sitting
                # in the OCA engine's "verify" (Waiting) state has been
                # computed but not confirmed — it is the same thing as the
                # Enterprise draft excluded in 22f68e1, and the Czech side has
                # always filtered on "done" alone. There is no "paid" state on
                # this engine.
                ("state", "=", "done"),
                ("id", "!=", self.id),
            ]
        )
        gross = 0.0
        hours = 0.0
        for slip in slips:
            for line in slip.line_ids:
                if line.code == "GROSS":
                    gross += line.total
                elif line.code in ("DOVOLENKA_NAHRADA", "OBSTACLE_NAHRADA",
                                   "PREKAZKA_NAHRADA"):
                    # náhrady are excluded from the priemerný-zárobok base
                    gross -= line.total
            for wd in slip.worked_days_line_ids:
                if wd.code == "WORK100":
                    hours += wd.number_of_hours
        min_hours = self.rule_parameter("l10n_sk_avg_earnings_min_hours")
        if hours >= min_hours and gross > 0.0:
            phz = round(gross / hours, 4)
        else:
            sched_hours = self.l10n_sk_scheduled_hours()
            phz = round(self.contract_id.wage / sched_hours, 4) if sched_hours else 0.0
        return max(phz, min_hourly)

    def l10n_sk_scheduled_days(self):
        """Full scheduled working days in the payslip period.

        Denominator for the partial-month proration of the basic wage: unlike
        ``worked_days.WORK100`` (which the engine clamps to the contract start
        date), this counts the working days of the WHOLE payslip period per the
        resource calendar, ignoring the contract start/end. For a full month the
        two are equal, so the basic wage is unchanged; for a mid-month hire or
        leaver the worked days are fewer and the wage is prorated.
        """
        self.ensure_one()
        contract = self.contract_id
        calendar = contract.resource_calendar_id
        if not calendar:
            return 0.0
        data = self.employee_id._get_work_days_data_batch(
            datetime.combine(self.date_from, time.min),
            datetime.combine(self.date_to, time.max),
            calendar=calendar,
            compute_leaves=False,
        )
        return data.get(self.employee_id.id, {}).get("days", 0.0)

    def l10n_sk_scheduled_hours(self):
        """Full scheduled working HOURS of the whole payslip period.

        Companion to :meth:`l10n_sk_scheduled_days`; used as the denominator of
        the probable-earnings (pravdepodobný zárobok) fallback.
        """
        self.ensure_one()
        calendar = self.contract_id.resource_calendar_id
        if not calendar:
            return 0.0
        data = self.employee_id._get_work_days_data_batch(
            datetime.combine(self.date_from, time.min),
            datetime.combine(self.date_to, time.max),
            calendar=calendar,
            compute_leaves=False,
        )
        return data.get(self.employee_id.id, {}).get("hours", 0.0)

    def _get_baselocaldict(self, contracts):
        # The payroll engine only injects ``math`` (via tools) into the
        # salary-rule namespace.  The Slovak income-tax rules need date helpers,
        # so we also expose ``relativedelta``.
        localdict = super()._get_baselocaldict(contracts)
        localdict["relativedelta"] = relativedelta
        return localdict
