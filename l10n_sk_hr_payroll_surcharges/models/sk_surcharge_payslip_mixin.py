# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The payslip half of the surcharge feature, kept engine-neutral.

Declared as an ``AbstractModel`` so the base module does not drag either
engine's ``hr.payslip`` into its dependencies; the two bridge modules mix it
into their engine's payslip and add the salary rules that call it.

Where the hours come from
-------------------------
Two sources, checked in this order for every surcharge code:

1. A **worked-days line** carrying that code. This is the good path — it means
   real work entries drove the hours. Only the Enterprise engine ships the
   ``hr_work_entry`` stack, so in practice this is the ``_dd`` bridge.
2. A **payslip input** carrying that code, whose ``amount`` is read as a
   number of hours.

Falling back rather than picking one keeps a site free to migrate from
hand-entered inputs to work entries per employee, and keeps the OCA engine
(which has no work-entry stack) working at all. Where both exist the worked
days win, because they are the auditable source.
"""

from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .surcharge_calc import (
    BASE_AVG_EARNINGS,
    SURCHARGE_BASE,
    SURCHARGE_CODES,
    min_wage_hourly,
    min_wage_topup_hourly,
    min_wage_topup_monthly,
    surcharge_amount,
    surcharge_pct,
)

# Worked-day codes that count as ordinary working time — the denominator of
# the minimum-wage comparison. Overtime is deliberately absent:
# § 120 ods. 3 keeps overtime out of the comparison on both sides.
ORDINARY_WORK_CODES = ("WORK100",)

# Absence codes the Slovak country modules put on their leave types. Only the
# OCA engine needs them subtracted — see ``_l10n_sk_work100_is_gross``.
ABSENCE_WORK_CODES = ("DOVOLENKA", "PN", "OCR", "NEPLATENE", "OBSTACLE")


class SkSurchargePayslipMixin(models.AbstractModel):
    _name = "sk.surcharge.payslip.mixin"
    _description = "Slovak Wage Surcharge Payslip Mixin"

    l10n_sk_surcharge_total = fields.Float(
        "Wage Surcharges",
        compute="_compute_l10n_sk_surcharge_total",
        help="Sum of every statutory wage surcharge on this payslip. Shown "
        "for reference; the individual amounts are separate payslip lines.",
    )

    def _compute_l10n_sk_surcharge_total(self):
        for slip in self:
            slip.l10n_sk_surcharge_total = sum(
                slip._l10n_sk_surcharge_amount(code) for code in SURCHARGE_CODES
            )

    # ------------------------------------------------------------------
    # engine adapters
    # ------------------------------------------------------------------
    def _l10n_sk_version(self):
        """The contract record, whatever this engine calls it.

        Enterprise names the payslip's contract ``version_id``; the OCA engine
        kept ``contract_id``. Both point at ``hr.version`` in Odoo 19.
        """
        self.ensure_one()
        if "version_id" in self._fields:
            return self.version_id
        return self.contract_id

    def _l10n_sk_avg_hourly(self):
        """Priemerný hodinový zárobok (§ 134), from the country module."""
        self.ensure_one()
        if not hasattr(self, "l10n_sk_average_hourly_earnings"):
            raise UserError(
                _(
                    "The average-earnings helper is missing. Install one of "
                    "the Slovak payroll modules (l10n_sk_hr_payroll_oca or "
                    "l10n_sk_hr_payroll_ee) — the holiday and overtime "
                    "surcharges are percentages of average earnings and "
                    "cannot be computed without it."
                )
            )
        return self.l10n_sk_average_hourly_earnings()

    # ------------------------------------------------------------------
    # hours
    # ------------------------------------------------------------------
    def _l10n_sk_surcharge_hours(self, code):
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

    def _l10n_sk_work100_is_gross(self):
        """Whether the ordinary-work line still contains absence hours.

        The two engines disagree, and getting this wrong silently overpays.
        The OCA engine's ``_compute_worked_days`` returns the FULL days the
        calendar schedules and documents that it "don't substract leaves by
        default", putting absences on separate (negative) lines. Enterprise
        instead groups real work entries by type, so a day of dovolenka never
        lands in ``WORK100`` at all. The ``_oca`` bridge overrides this.
        """
        return False

    def _l10n_sk_absence_hours(self):
        """Absence hours recorded on this payslip, as a positive number."""
        self.ensure_one()
        return sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code in ABSENCE_WORK_CODES
        )

    def _l10n_sk_ordinary_hours(self):
        """Hours actually worked in ordinary working time.

        The minimum-wage comparison pairs this with the wage that was actually
        paid, so it must be NET of absences: an employee absent all month has
        their basic wage prorated to zero, and pairing that zero with a full
        month of hours would claim the entire monthly minimum wage as a
        top-up for someone who did not work.

        Falls back to the scheduled hours of the period only when the payslip
        carries no worked-days lines at all. Both engines have that state —
        the OCA engine builds worked days from an onchange, Enterprise skips
        them under ``salary_simulation`` — and in it both pay the full monthly
        wage, so pairing it with the full month's hours is right. The test is
        deliberately on the presence of lines rather than on the hours being
        non-zero: a full month of absence legitimately yields zero hours, and
        falling back there would resurrect the bug above.
        """
        self.ensure_one()
        if not self.worked_days_line_ids:
            return self._l10n_sk_scheduled_hours()
        hours = sum(
            abs(line.number_of_hours)
            for line in self.worked_days_line_ids
            if line.code in ORDINARY_WORK_CODES
        )
        if self._l10n_sk_work100_is_gross():
            hours -= self._l10n_sk_absence_hours()
        return max(0.0, hours)

    def _l10n_sk_calendar_hours(self, calendar):
        """Working hours *calendar* schedules across the payslip period."""
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

    def _l10n_sk_scheduled_hours(self):
        """Hours THIS contract schedules in the period, ignoring absences."""
        self.ensure_one()
        return self._l10n_sk_calendar_hours(
            self._l10n_sk_version().resource_calendar_id
        )

    def _l10n_sk_full_time_hours(self):
        """Hours a FULL-TIME contract would schedule in the same period.

        The denominator of the § 120 ods. 4 proration, and deliberately not
        the employee's own schedule: prorating a part-timer against their own
        calendar always yields a ratio of 1 and would hold them to the full
        monthly minimum wage, which is precisely backwards. Measuring against
        the company's standard calendar makes a half-timer owe half the claim
        and leaves a full-timer unaffected.
        """
        self.ensure_one()
        company_calendar = self.company_id.resource_calendar_id
        return self._l10n_sk_calendar_hours(company_calendar) or (
            self._l10n_sk_scheduled_hours()
        )

    # ------------------------------------------------------------------
    # money — called from the salary rules
    # ------------------------------------------------------------------
    def _l10n_sk_surcharge_rates(self):
        self.ensure_one()
        return self.env["l10n.sk.wage.surcharge.rate"]._get_rate(self.date_to)

    def _l10n_sk_min_wage_base_hourly(self):
        """Level-1 hourly minimum wage — the base of most surcharges.

        Deliberately NOT the employee's own stupeň náročnosti: §§ 122a–123
        all say ``minimálnej mzdy v eurách za hodinu``, the plain figure, so a
        senior employee's higher wage claim does not inflate their night
        surcharge.
        """
        self.ensure_one()
        return self.env["l10n.sk.minimum.wage"]._get_base_hourly(self.date_to)

    def _l10n_sk_surcharge_pct(self, code):
        """Percentage for *code* given this contract's flags."""
        self.ensure_one()
        version = self._l10n_sk_version()
        risk = bool(version.l10n_sk_risk_work)
        reduced = bool(
            {
                "NOC": version.l10n_sk_night_reduced,
                "SOBOTA": version.l10n_sk_saturday_reduced,
                "NEDELA": version.l10n_sk_sunday_reduced,
            }.get(code)
        )
        rates = self._l10n_sk_surcharge_rates()._rates_dict()
        return surcharge_pct(rates, code, risk=risk, reduced=reduced)

    def _l10n_sk_surcharge_amount(self, code):
        """Money for surcharge *code* on this payslip, as a positive number.

        This is the *mzdové zvýhodnenie* only — the uplift the law mandates on
        top of the wage for the hour. The wage for the hour itself is already
        in BASIC for night / Saturday / Sunday / difficult / holiday work.
        Overtime is the exception and gets its own base-pay rule, because
        overtime hours by definition fall outside the scheduled time a monthly
        salary pays for.
        """
        self.ensure_one()
        hours = self._l10n_sk_surcharge_hours(code)
        if not hours:
            return 0.0
        if SURCHARGE_BASE[code] == BASE_AVG_EARNINGS:
            hourly = self._l10n_sk_avg_hourly()
        else:
            hourly = self._l10n_sk_min_wage_base_hourly()
        return surcharge_amount(hours, hourly, self._l10n_sk_surcharge_pct(code))

    def _l10n_sk_overtime_base_amount(self):
        """Wage for the overtime hours themselves, at average earnings.

        § 121 ods. 1 entitles the employee to ``mzda a mzdové zvýhodnenie``.
        The uplift is ``_l10n_sk_surcharge_amount('NADCAS')``; this is the
        wage part. Average earnings are used as the hourly rate, which is the
        common Slovak practice for a monthly-salaried employee whose
        contractual hourly rate is not stated.
        """
        self.ensure_one()
        hours = self._l10n_sk_surcharge_hours("NADCAS")
        if not hours:
            return 0.0
        return surcharge_amount(hours, self._l10n_sk_avg_hourly(), 100.0)

    # ------------------------------------------------------------------
    # minimum wage claim (stupeň náročnosti)
    # ------------------------------------------------------------------
    def _l10n_sk_min_wage_claim(self):
        """The minimum-wage claim record for this contract's level."""
        self.ensure_one()
        version = self._l10n_sk_version()
        return self.env["l10n.sk.minimum.wage"]._get_claim(
            self.date_to, version.l10n_sk_wage_level or "1"
        )

    def _l10n_sk_min_wage_hourly_claim(self):
        """This contract's hourly minimum-wage claim, § 120 ods. 4 and 5."""
        self.ensure_one()
        calendar = self._l10n_sk_version().resource_calendar_id
        return min_wage_hourly(
            self._l10n_sk_min_wage_claim().amount_hourly,
            calendar.full_time_required_hours if calendar else 0.0,
            self._l10n_sk_surcharge_rates().standard_weekly_hours,
        )

    def _l10n_sk_min_wage_claim_applies(self):
        """Whether § 120 minimum wage claims apply to this contract.

        Delegates to the applicability table in l10n_sk_hr_payroll_base rather
        than re-deriving it. Re-deriving is how this module came to top a
        dohodár's wage up to a full-time monthly claim while the contract-level
        warning, two files away, correctly declined to warn about it.
        """
        self.ensure_one()
        version = self._l10n_sk_version()
        if not version:
            # A payslip with no contract attached — the OCA engine does not
            # derive one, so its reporting fixtures leave it empty. Nothing
            # marks such a slip as an agreement, so treat it as employment,
            # which is what this did before the table was consulted.
            return True
        return version.l10n_sk_applies("MIN_WAGE_CLAIM")

    def _l10n_sk_is_hourly_paid(self):
        """Whether the contract states an hourly rate rather than a salary.

        Only the OCA Slovak module models hourly workers today, so the field
        is probed rather than assumed — the Enterprise side simply has no
        hourly contracts to distinguish.
        """
        self.ensure_one()
        version = self._l10n_sk_version()
        if "l10n_sk_hourly_wage" not in version._fields:
            return False
        return bool(version.l10n_sk_hourly_wage)

    def _l10n_sk_min_wage_topup(self, qualifying_wage):
        """Doplatok bringing *qualifying_wage* up to the statutory claim.

        The caller passes the wage that counts for the comparison. Every
        surcharge this module computes, the overtime base pay and the wage
        replacements are excluded by § 120 ods. 3 — see the salary rule, which
        subtracts them before calling here.

        Monthly-paid and hourly-paid employees are measured against different
        figures; see ``min_wage_topup_monthly`` for why conflating them
        invents a top-up in any month scheduling more than 174 hours.

        Returns nothing for a work agreement. § 120 sets minimum wage claims
        for a pracovný pomer; a dohodár is entitled to the minimum HOURLY wage
        under zák. 663/2007 instead, and has no stupeň náročnosti to be
        measured against. Topping a dohodár's monthly remuneration up to a
        full-time monthly claim would invent an entitlement they do not have.
        """
        self.ensure_one()
        if not self._l10n_sk_min_wage_claim_applies():
            return 0.0
        if self._l10n_sk_is_hourly_paid():
            return min_wage_topup_hourly(
                qualifying_wage,
                self._l10n_sk_ordinary_hours(),
                self._l10n_sk_min_wage_hourly_claim(),
            )
        return min_wage_topup_monthly(
            qualifying_wage,
            self._l10n_sk_ordinary_hours(),
            self._l10n_sk_full_time_hours(),
            self._l10n_sk_min_wage_claim().amount_monthly,
        )

    @api.model
    def _l10n_sk_surcharges_enabled(self, company):
        return company.country_id.code == "SK"
