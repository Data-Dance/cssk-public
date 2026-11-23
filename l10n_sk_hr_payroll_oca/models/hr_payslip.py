# Copyright 2026 Data Dance s.r.o.
# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar as _calendar
from datetime import date, datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_round

from odoo.addons.l10n_sk_hr_payroll_base.meal_days import (
    count_meal_days,
    whole_days,
)
from odoo.addons.l10n_sk_hr_payroll_base.public_holiday import (
    absence_keeps_public_holiday,
)
from odoo.addons.l10n_sk_hr_payroll_base.sick_pay import (
    merge_spans,
    round_sick_pay,
    sick_pay_amount,
    split_sick_days,
)
from odoo.addons.l10n_sk_hr_payroll_base.worked_days import worked_day_totals

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

    def _l10n_sk_version(self):
        """The contract (``hr.version``) the payslip is computed on.

        OCA payroll fills ``contract_id`` only in the form's onchange and in
        the batch wizard; a payslip created through the API leaves it empty
        while ``compute_sheet`` still resolves the employee's contract for the
        rules. Fall back to that same resolution.
        """
        self.ensure_one()
        return self.contract_id or self._get_employee_contracts()[:1]

    def _l10n_sk_monthly_cash_wage(self, contract):
        """Resolve the monthly wage input without changing the contract.

        Extensions can supply a payslip-specific input while retaining the
        native absence, calendar, insurance and tax calculation. This must be
        a pure function of the payslip and the supplied contract: dated wage
        segments can resolve it more than once.
        """
        self.ensure_one()
        return contract.wage

    def l10n_sk_basic_salary(self, contract, worked_days, scheduled_hours=None):
        """Compute BASIC through a cooperative country-level salary hook.

        ``worked_days`` is the engine's WorkedDays object. An integration
        processing a dated wage segment can supply that segment's full-period
        calendar divisor; the default keeps the existing payslip calculation.
        Tax and insurance rules still run once on the resulting BASIC amount.
        The amount is returned before rounding, hourly pay included; the
        BASIC rule rounds it up to the cent once.
        """
        self.ensure_one()
        absence = sum(
            abs(worked_days.dict[code].number_of_hours)
            for code in self.l10n_sk_absence_codes()
            if code in worked_days.dict
        )
        if contract.l10n_sk_hourly_wage:
            if "WORK100" not in worked_days.dict:
                return 0.0
            hours = worked_days.WORK100.number_of_hours
            # Never negative, even when inconsistent leave data exceeds WORK100.
            return max(0.0, hours - absence) * contract.l10n_sk_hourly_wage
        monthly_wage = self._l10n_sk_monthly_cash_wage(contract)
        result = monthly_wage
        if "WORK100" in worked_days.dict:
            scheduled = (
                self.l10n_sk_scheduled_hours()
                if scheduled_hours is None
                else scheduled_hours
            )
            paid_worked = worked_days.WORK100.number_of_hours - absence
            if scheduled and paid_worked < scheduled:
                result = monthly_wage * paid_worked / scheduled
        return result

    def l10n_sk_round_cent(self, amount):
        """Round to the cent, a following five or more upward.

        The rounding of § 47 zákona 595/2003 Z. z., and the one a payslip
        line is stored with. For the tax advance and the child bonus; a wage
        component is rounded by ``l10n_sk_round_wage_component``.
        """
        return float_round(amount, precision_digits=2)

    def l10n_sk_absence_codes(self):
        """The worked-day codes that count as an absence, for the BASIC rule.

        Exposed as a method so the rule body can read the list instead of
        carrying its own copy: it used to be duplicated in the XML, which meant
        adding an absence type in one place and forgetting the other silently
        stopped prorating the wage for it.
        """
        return L10N_SK_ABSENCE_CODES

    def l10n_sk_input_amount(self, code):
        """Sum of every input line with ``code``.

        The engine hands the rules one input line per code, so a rule that
        reads ``inputs.CODE.amount`` sees only one of several lines.
        """
        self.ensure_one()
        return sum(
            line.amount for line in self.input_line_ids if line.code == code
        )

    def l10n_sk_input_name(self, code):
        """The names of the input lines with ``code``, each once."""
        self.ensure_one()
        names = []
        for line in self.input_line_ids:
            if line.code == code and line.name and line.name not in names:
                names.append(line.name)
        return ", ".join(names)

    def l10n_sk_meal_days(self):
        """The days of the period that earn a meal.

        § 152 ods. 2 Zákonníka práce gives the meal to an employee who works
        more than four hours within the shift (``l10n_sk_meal_min_hours``).
        Each scheduled day is decided alone: its scheduled hours less the
        hours of absence and of a public holiday on that day. Overtime is an
        input with hours and no day here, so it is not in the hours of a day.
        With *Meal also for a Shift of Four Hours or Less* on the contract
        (§ 152 ods. 9) a day with any work on it earns the meal.

        Worked-day lines that do not hold what the calendar and the absences
        give were typed by hand or are older than an absence. The days they
        hold cannot be placed in the calendar: their whole days count.
        """
        self.ensure_one()
        worked = self._l10n_sk_hours_worked_by_day()
        if worked is None:
            scheduled, not_worked = self._l10n_sk_worked_day_line_totals("number_of_days")
            return whole_days(scheduled - not_worked)
        return count_meal_days(
            worked.values(),
            self.rule_parameter("l10n_sk_meal_min_hours"),
            # The employer gives the meal on a shorter shift too (§ 152 ods. 9).
            any_work=bool(self._l10n_sk_version().l10n_sk_meal_short_shift),
        )

    def _l10n_sk_worked_day_line_totals(self, field):
        """``(scheduled, not worked)`` of the worked-day lines, in ``field``.

        WORK100 is the whole schedule of the period; the absences and the
        public holidays (the engine's GLOBAL line) are the time not worked.
        """
        self.ensure_one()
        scheduled = not_worked = 0.0
        absence_codes = self.l10n_sk_absence_codes() + ("GLOBAL",)
        for line in self.worked_days_line_ids:
            if line.code == "WORK100":
                scheduled += line[field]
            elif line.code in absence_codes:
                not_worked += abs(line[field])
        return scheduled, not_worked

    def _l10n_sk_hours_worked_by_day(self):
        """Hours worked on each scheduled day of the payslip: ``{day: hours}``.

        The schedule and the time off are read the way the worked-day lines
        are built (``get_worked_day_lines``), day by day. ``None`` when the
        payslip's lines hold other hours than that: the lines are what the
        payslip pays, and they do not say which day.
        """
        self.ensure_one()
        contract = self._l10n_sk_version()
        if len(contract) != 1 or not contract.resource_calendar_id:
            return None
        first, last = self.date_from, self.date_to
        # The contract dates are HR-manager fields.
        start, end = contract.date_start, contract.sudo().date_end
        if start and start > first:
            first = start
        if end and end < last:
            last = end
        scheduled = {}
        time_off = {}
        if first <= last:
            contract = self._l10n_sk_whole_schedule(contract)
            day_from = datetime.combine(first, time.min)
            day_to = datetime.combine(last, time.max)
            resource = contract.employee_id.resource_id
            # As in _l10n_sk_leave_pieces: naive bounds are read as UTC.
            attendances = contract.resource_calendar_id._attendance_intervals_batch(
                day_from.replace(tzinfo=pytz.utc),
                day_to.replace(tzinfo=pytz.utc),
                resource,
            )[resource.id]
            for begin, stop, _records in attendances:
                day = begin.date()
                scheduled[day] = (
                    scheduled.get(day, 0.0) + (stop - begin).total_seconds() / 3600
                )
            for day, hours, _leave_type in self._l10n_sk_leave_pieces(
                contract, day_from, day_to
            ):
                time_off[day] = time_off.get(day, 0.0) + hours
        line_scheduled, line_not_worked = self._l10n_sk_worked_day_line_totals(
            "number_of_hours"
        )
        if (
            abs(sum(scheduled.values()) - line_scheduled) > 0.01
            or abs(sum(time_off.values()) - line_not_worked) > 0.01
        ):
            return None
        return {
            day: hours - time_off.get(day, 0.0) for day, hours in scheduled.items()
        }

    def rule_parameter(self, code):
        """Accessor for dated statutory parameters.

        Returns the value of the ``hr.rule.parameter`` with ``code`` that is
        effective at the payslip ``date_to``.
        """
        self.ensure_one()
        return self.env["hr.rule.parameter"]._get_parameter_value(code, self.date_to)

    def _l10n_sk_monthly_tax_facts(self, version, *, include_january=False):
        """Read detached facts for monthly allowance and evidence consumers.

        January lookup is opt-in so an unsigned declaration keeps its native
        early exit. Extensions may supply checked, owned facts through this
        cooperative reader; a caller dictionary or context is not authority.
        The default reads the actual native contract and January version.
        """
        self.ensure_one()
        if (
            version.employee_id != self.employee_id
            or version.company_id != self.company_id
        ):
            raise UserError(
                _(
                    "Use the employee and company contract version for the monthly pension tax profile."
                )
            )
        facts = {
            "company": self.company_id.id,
            "employee": self.employee_id.id,
            "version": version.id,
            "year": self.date_to.year if self.date_to else False,
            "as_of": self.date_to.isoformat() if self.date_to else False,
            "signed": bool(version.l10n_sk_tax_declaration_signed),
            "january": False,
        }
        if include_january:
            historical = self.employee_id._l10n_sk_january_tax_version(
                self.date_to.year, self.company_id, self.date_to
            )
            if historical:
                facts["january"] = {
                    "version": historical.id,
                    "company": historical.company_id.id,
                    "date": (
                        historical.date_version.isoformat()
                        if historical.date_version
                        else False
                    ),
                    "tax_pensioner": bool(historical.l10n_sk_tax_pensioner),
                    "insurance_pension": historical.l10n_sk_pension_type or False,
                    "pension_annual": float(historical.l10n_sk_nczd_pension_annual),
                }
        return facts

    def l10n_sk_monthly_nczd(self, version):
        """Sections 35/36 and 11(6), FS FAQ 7/9: no January-pension allowance.

        The annual difference for a small pension belongs in RZD/personal DP.
        Keep this eligibility hook separate from dated statutory parameters.
        """
        self.ensure_one()
        if version.employee_id != self.employee_id or version.company_id != self.company_id:
            raise UserError(_("Use the employee and company contract version for the monthly pension tax profile."))
        if self._l10n_sk_tax_principal():
            # Taxed on another record's payslip, where the one non-taxable
            # amount of the month is applied (§ 35 ods. 1 písm. b)).
            return 0.0
        if not self._l10n_sk_monthly_tax_facts(version)["signed"]:
            return 0.0
        historical = self._l10n_sk_monthly_tax_facts(version, include_january=True)["january"]
        if historical:
            if historical["company"] != self.company_id.id:
                raise UserError(_("Review the employee's 1 January pension version in the payroll company."))
            if historical["tax_pensioner"]:
                return 0.0
            if (historical["insurance_pension"] in ("old_age", "early_old_age", "service_at_age")
                    or historical["pension_annual"] > 0):
                raise UserError(_("The 1 January version indicates a pension. Review its tax-relevant pension flag against the retained declaration."))
        return self.rule_parameter("l10n_sk_nczd_monthly")

    def _l10n_sk_monthly_taxable_wage_round(self, amount):
        """Round the taxable wage if needed, before applying any band.

        Native TAXBASE is already in cents. Extensions handling sub-cent
        bases round the taxable wage half up under § 47, without flooring
        or rounding individual bands.
        """
        return amount

    def _l10n_sk_monthly_income_tax(self, base, version):
        """Return the negative monthly advance before final rounding.

        Pass the full whole-cent monthly base in EUR unless an extension
        rounds the taxable wage to cents. The caller aggregates the base
        before applying the allowance once and rounds the result once: the
        INCOMETAX rule passes ``_l10n_sk_monthly_tax_base``, which for a
        record that taxes the month for others holds the bases taken over
        and for a linked record is zero.
        """
        self.ensure_one()
        # The annual high-income taper remains an RZD matter. January pension
        # eligibility is handled by the existing monthly allowance reader.
        nczd = self.l10n_sk_monthly_nczd(version)
        taxable = self._l10n_sk_monthly_taxable_wage_round(max(0.0, base - nczd))
        bands = self.rule_parameter("l10n_sk_income_tax_bands")
        tax = 0.0
        prev = 0.0
        for rate, ceiling in bands:
            if taxable > prev:
                amt = min(taxable, ceiling) - prev
                tax += amt * rate
            prev = ceiling
        return -tax

    def _l10n_sk_is_slovak(self):
        """Whether the payslip is computed on a Slovak structure or company."""
        self.ensure_one()
        country = self.struct_id.country_id or self.company_id.country_id
        return country.code == "SK"

    def compute_sheet(self):
        # A rule's safe_eval wraps UserError in a Python traceback. Validate
        # before evaluation so the payroll officer gets the business message.
        for slip in self:
            version = slip._l10n_sk_version()
            if len(version) == 1 and slip.struct_id.country_id.code == "SK":
                slip.l10n_sk_monthly_nczd(version)
        return super().compute_sheet()

    # ------------------------------------------------------------------
    # Worked days
    # ------------------------------------------------------------------
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """End the worked-day lines of a Slovak contract with the contract.

        The engine starts them at the contract start and runs them to the end
        of the period. BASIC is the wage for the scheduled hours inside the
        contract, so the month it ends in needs them cut at its end too.
        """
        lines = []
        for contract in contracts:
            last = date_to
            # The contract dates are HR-manager fields.
            contract_end = contract.sudo().date_end
            if (
                self._l10n_sk_is_slovak_contract(contract)
                and contract_end
                and contract_end < last
            ):
                last = contract_end
            lines.extend(super().get_worked_day_lines(contract, date_from, last))
        return lines

    @api.model
    def _l10n_sk_is_slovak_contract(self, contract):
        country = contract.struct_id.country_id or contract.company_id.country_id
        return country.code == "SK"

    @api.model
    def _l10n_sk_whole_schedule(self, contract):
        """The contract as the rules need it: with the whole schedule.

        The engine asks the calendar to leave public holidays out
        (``exclude_public_holidays``, honoured by ``hr_holidays_public``).
        WORK100 is the whole schedule of the period here, the same hours
        BASIC divides by, and a public holiday is inside a monthly wage
        (§ 122 ods. 3 Zákonníka práce); it reaches the payslip as a public
        holiday of the working calendar, on the ``GLOBAL`` line.
        """
        if self._l10n_sk_is_slovak_contract(contract):
            return contract.with_context(exclude_public_holidays=False)
        return contract

    def _compute_worked_days(self, contract, day_from, day_to):
        return super()._compute_worked_days(
            self._l10n_sk_whole_schedule(contract), day_from, day_to
        )

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
        ``payroll/models/hr_payslip.py:_compute_leave_days`` (OCA 18.0); the
        ``code``/``sequence`` source is changed, and each piece of absence is
        given to the leave that covers it (``_l10n_sk_leave_pieces``).
        """
        from pytz import timezone

        contract = self._l10n_sk_whole_schedule(contract)
        leaves_positive = (
            self.env["ir.config_parameter"].sudo().get_param("payroll.leaves_positive")
        )
        leaves = {}
        calendar = contract.resource_calendar_id
        tz = timezone(calendar.tz or contract.employee_id.tz or "UTC")
        day_leave_intervals = self._l10n_sk_leave_pieces(contract, day_from, day_to)
        for day, hours, leave_type in day_leave_intervals:
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

    def _l10n_sk_leave_pieces(self, contract, day_from, day_to):
        """The scheduled time off work as ``(day, hours, leave type)`` pieces.

        ``list_leaves`` merges the leaves that overlap into one interval that
        carries all their records, so a public holiday at the start of a
        sickness and the sickness arrive as one block. Each piece of the
        schedule is cut here at the bounds of those records and given to the
        leave that really covers it. Where a public holiday of the calendar
        and an absence cover the same time, the absence keeps it only if it
        is one of ``ABSENCES_OVER_A_PUBLIC_HOLIDAY``; otherwise the time is
        the holiday (an empty leave type, the engine's ``GLOBAL`` line),
        which is not a day of leave (§ 112 ods. 3 Zákonníka práce) and is
        inside a monthly wage (§ 122 ods. 3).

        A block with no Slovak absence in it is filed as the engine files
        it, by its first record.
        """
        from pytz import utc

        employee = contract.employee_id
        resource = employee.resource_id
        calendar = contract.resource_calendar_id
        start = day_from if day_from.tzinfo else day_from.replace(tzinfo=utc)
        end = day_to if day_to.tzinfo else day_to.replace(tzinfo=utc)
        attendances = calendar._attendance_intervals_batch(start, end, resource)[
            resource.id
        ]
        time_off = calendar._leave_intervals_batch(start, end, resource)[resource.id]
        no_type = self.env["hr.leave.type"]
        pieces = []
        for piece_start, piece_stop, records in time_off & attendances:
            first_type = records[:1].holiday_id.holiday_status_id
            if not any(
                record.holiday_id.holiday_status_id.l10n_sk_payroll_code
                for record in records
            ):
                hours = (piece_stop - piece_start).total_seconds() / 3600
                pieces.append((piece_start.date(), hours, first_type))
                continue
            bounds = [
                (record, utc.localize(record.date_from), utc.localize(record.date_to))
                for record in records
            ]
            cuts = {piece_start, piece_stop}
            for _record, record_start, record_stop in bounds:
                cuts.update(
                    moment
                    for moment in (record_start, record_stop)
                    if piece_start < moment < piece_stop
                )
            cuts = sorted(cuts)
            for cut_start, cut_stop in zip(cuts, cuts[1:], strict=False):
                covering = [
                    record
                    for record, record_start, record_stop in bounds
                    if record_start < cut_stop and record_stop > cut_start
                ]
                absences = [record for record in covering if record.holiday_id]
                leave_type = absences[0].holiday_id.holiday_status_id if absences else no_type
                public_holiday = any(
                    not record.resource_id and not record.holiday_id
                    for record in covering
                )
                if (
                    absences
                    and public_holiday
                    and not absence_keeps_public_holiday(leave_type.l10n_sk_payroll_code)
                ):
                    leave_type = no_type
                hours = (cut_stop - cut_start).total_seconds() / 3600
                pieces.append((cut_start.date(), hours, leave_type))
        return pieces

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

    def _l10n_sk_average_payslips(self):
        """Confirmed sources in this company and the determining quarter.

        Extensions that retain superseded financial originals can filter the
        recordset here without duplicating the statutory average calculation.
        """
        self.ensure_one()
        q_start, q_end = self._l10n_sk_previous_quarter()
        slips = self.search([('employee_id', '=', self.employee_id.id),
            ('company_id', '=', self.company_id.id), ('date_from', '>=', q_start),
            ('date_to', '<=', q_end), ('state', '=', 'done'), ('id', 'not in', self._origin.ids)])
        version = self._l10n_sk_version()
        if version.contract_date_start:
            # A wage/version change within one employment keeps its start;
            # a genuine rehire starts a separate employment (§134 ods. 7).
            slips = slips.filtered(lambda slip:
                slip._l10n_sk_version().contract_date_start == version.contract_date_start)
        return slips

    def _l10n_sk_average_counted_wage(self):
        """Wage basis before credit-note sign; cooperative classification hook."""
        self.ensure_one()
        replacements = ('DOVOLENKA_NAHRADA', 'OBSTACLE_NAHRADA', 'PREKAZKA_NAHRADA')
        return sum(line.total for line in self.line_ids if line.code == 'GROSS') - sum(
            line.total for line in self.line_ids if line.code in replacements)

    def _l10n_sk_average_worked_time(self):
        """Worked days/hours before credit-note sign, excluding absences."""
        self.ensure_one()
        worked = self.worked_days_line_ids.filtered(lambda line: line.code == "WORK100")
        # OCA WORK100 is the full scheduled time; leave is separate. The
        # payroll.leaves_positive setting changes the leave sign, not whether
        # an absence was worked. Reuse the country module's shared taxonomy.
        absences = self.worked_days_line_ids.filtered(
            lambda line: line.code in self.l10n_sk_absence_codes()
        )
        return (
            sum(worked.mapped("number_of_days"))
            - sum(abs(line.number_of_days) for line in absences),
            sum(worked.mapped("number_of_hours"))
            - sum(abs(line.number_of_hours) for line in absences),
        )

    def l10n_sk_average_hourly_earnings(self):
        """Priemerný hodinový zárobok per §134 Zákonníka práce (č. 311/2001).

        Rozhodujúce obdobie = the previous calendar quarter. The average hourly
        earnings = gross wage credited in that quarter (EXCLUDING wage
        replacements / náhrady) ÷ hours worked in that quarter, rounded to 4
        decimals. If the employee did not work at least 21 days or 168 hours in the
        determining period (§134 ods. 3) the probable earnings (pravdepodobný
        zárobok) are used instead — here the reviewed monthly wage over the
        month's scheduled hours. Finally the statutory floor applies: if the
        result is below the hourly minimum wage it is raised to it (§134 ods. 5).

        Sources: podnikajte.sk "Priemerný zárobok (dovolenkový priemer)"
        <https://www.podnikajte.sk/zamestnanci-a-hr/priemerny-zarobok-dovolenkovy-priemer>,
        Národný inšpektorát práce <https://www.ip.gov.sk/faq/104739/>,
        §134 zákona č. 311/2001 Z. z. (Zákonník práce).

        The counted wage defaults to GROSS less the SK náhrada lines, rather
        than a from-scratch §118 classification. Extensions can classify
        additional wage/nonwage components through the counted-wage hook.
        """
        self.ensure_one()
        min_hourly = self.rule_parameter("l10n_sk_min_hourly_wage")
        gross = days = hours = 0.0
        for slip in self._l10n_sk_average_payslips():
            sign = -1 if slip.credit_note else 1
            gross += sign * slip._l10n_sk_average_counted_wage()
            worked_days, worked_hours = slip._l10n_sk_average_worked_time()
            days += sign * worked_days
            hours += sign * worked_hours
        min_hours = self.rule_parameter("l10n_sk_avg_earnings_min_hours")
        if (days >= 21 or hours >= min_hours) and hours > 0.0 and gross > 0.0:
            phz = round(gross / hours, 4)
        else:
            sched_hours = self.l10n_sk_scheduled_hours()
            contract = self._l10n_sk_version()
            if contract.l10n_sk_hourly_wage:
                # What an hourly-paid employee would earn in an hour is the rate.
                phz = round(contract.l10n_sk_hourly_wage, 4)
            else:
                phz = round(self._l10n_sk_monthly_cash_wage(contract) / sched_hours, 4) if sched_hours else 0.0
        return max(phz, min_hourly)

    def l10n_sk_scheduled_days(self):
        """Full scheduled working days in the payslip period.

        Denominator for the partial-month proration of the basic wage: unlike
        ``worked_days.WORK100`` (which is cut at the contract start and end),
        this counts the working days of the WHOLE payslip period per the
        resource calendar, ignoring the contract start/end. For a full month the
        two are equal, so the basic wage is unchanged; for a mid-month hire or
        leaver the worked days are fewer and the wage is prorated.
        """
        self.ensure_one()
        contract = self._l10n_sk_version()
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

    def l10n_sk_pn_split(self, tier1_days, employer_days):
        """Calendar-day sick-pay split for this payslip, from the PN leaves.

        Returns ``(tier1, tier2, calendar_days)``, or ``False`` when no
        validated PN leave reaches the period and the caller must use its
        manual inputs.
        """
        spans = self._l10n_sk_pn_spans()
        if spans is False:
            return False
        first, last = self._l10n_sk_pn_payment_period()
        return split_sick_days(spans, first, last, tier1_days, employer_days)

    def _l10n_sk_pn_spans(self):
        """Keep the actual incapacity onset, including its preceding month."""
        self.ensure_one()
        leaves = (
            self.env["hr.leave"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("state", "=", "validate"),
                    ("request_date_from", "<=", self.date_to),
                    ("request_date_to", ">=", self.date_from - timedelta(days=366)),
                    ("holiday_status_id.l10n_sk_payroll_code", "=", "PN"),
                ]
            )
        )
        spans = [(x.request_date_from, x.request_date_to) for x in leaves]
        if not any(
            start <= self.date_to and end >= self.date_from for start, end in spans
        ):
            return False
        return merge_spans(spans)

    def _l10n_sk_pn_payment_period(self):
        """The employer stops paying when its insured relationship ends."""
        version = self._l10n_sk_version()
        first, last = self.date_from, self.date_to
        if version.contract_date_start:
            first = max(first, version.contract_date_start)
        if version.contract_date_end:
            last = min(last, version.contract_date_end)
        return first, last

    def l10n_sk_pn_compensation(self, daily_base):
        """Value native PN episodes using each episode's dated statutory terms.

        A claim beginning in 2025 retains its ten-day employer limit in 2026.
        Clipping the payable window must not restart the illness-day count.
        ``False`` means no native episode; zero is an actual native result.
        """
        spans = self._l10n_sk_pn_spans()
        if spans is False:
            return False
        first, last = self._l10n_sk_pn_payment_period()
        total = 0
        for start, end in spans:
            if start > last or end < first:
                continue

            def parameter(code):
                return self.env["hr.rule.parameter"]._get_parameter_value(code, start)

            tier1_days = parameter("l10n_sk_pn_tier1_days")
            employer_days = parameter("l10n_sk_pn_employer_days")
            tier1, tier2, _calendar_days = split_sick_days(
                [(start, end)], first, last, tier1_days, employer_days
            )
            capped_base = min(
                self._l10n_sk_pn_episode_base(daily_base, start),
                parameter("l10n_sk_pn_max_dvz"))
            rate1 = parameter("l10n_sk_pn_rate_tier1") / 100.0
            rate2 = parameter("l10n_sk_pn_rate_tier2") / 100.0
            total += sick_pay_amount(capped_base, tier1, tier2, rate1, rate2)
        return round_sick_pay(total)

    def _l10n_sk_dvz_confirmed_states(self):
        return ("done",)

    def _l10n_sk_leave_code_field(self):
        return "holiday_status_id.l10n_sk_payroll_code"

    def l10n_sk_pn_manual_compensation(self, daily_base, tier1, tier2, rate1, rate2):
        """Keep the existing manual fallback on the same statutory rounding."""
        return round_sick_pay(sick_pay_amount(daily_base, tier1, tier2, rate1, rate2))

    def l10n_sk_scheduled_hours(self):
        """Full scheduled working HOURS of the whole payslip period.

        Companion to :meth:`l10n_sk_scheduled_days`; used as the denominator of
        the probable-earnings (pravdepodobný zárobok) fallback.
        """
        self.ensure_one()
        calendar = self._l10n_sk_version().resource_calendar_id
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
        if self._l10n_sk_is_slovak():
            localdict["worked_days"].dict.update(self._l10n_sk_worked_day_totals())
        return localdict

    def _l10n_sk_worked_day_totals(self):
        """``{code: the lines as one}`` for each code with several lines.

        The engine hands the rules one worked-day line per code. Each leave
        type has a line of its own and several leave types share a payroll
        code, and a line can be typed by hand, so a code can have several
        lines: the rules then read their total.
        """
        self.ensure_one()
        return worked_day_totals(self.worked_days_line_ids)
