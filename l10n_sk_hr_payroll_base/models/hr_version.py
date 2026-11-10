# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Expose the applicability table to the salary rules of both engines.

``hr.version`` is core ``hr`` in Odoo 19, and the salary-rule namespace of both
engines hands the version to every rule — as ``contract`` on the OCA engine and
``version`` on Enterprise — so a method here is reachable from a rule condition
on either without this module knowing which engine is installed.
"""

from calendar import monthrange

from odoo import models
from odoo.tools import float_round

from ..applicability import EMPLOYMENT, applies
from ..social_assessment import assessment_base


class HrVersion(models.Model):
    _inherit = "hr.version"

    def l10n_sk_social_assessment_base(self, gross, ceiling=None, deduction=0):
        """One arithmetic source; callers select the fund's cap and deduction."""
        self.ensure_one()
        return assessment_base(gross, ceiling, deduction)

    def l10n_sk_social_fund_base(self, gross, code, monthly_cap, day, oop=0):
        """The exact base used by one social salary rule, before its rate.

        Applicability remains in the existing salary-rule conditions. The
        declaration records zero for a fund whose rule did not apply.
        """
        self.ensure_one()
        employee_codes = {"SICK", "PENSION", "DISABILITY", "UNEMPLOYMENT"}
        pension_codes = {
            "PENSION",
            "DISABILITY",
            "PENSIONEMPLOYER",
            "DISABILITYEMPLOYER",
            "RESERVEFUNDEMPLOYER",
        }
        known = (
            employee_codes
            | pension_codes
            | {
                "SICKEMPLOYER",
                "UNEMPLOYMENTEMPLOYER",
                "SHORTTIMEEMPLOYER",
                "ACCIDENT",
                "GUARANTEEEMPLOYER",
            }
        )
        if code not in known:
            raise ValueError("Unknown social-insurance salary code")
        if code == "GUARANTEEEMPLOYER" and getattr(
            self, "l10n_sk_guarantee_exempt", False
        ):
            return 0.0
        ceiling = (
            None
            if code == "ACCIDENT"
            else self.l10n_sk_employee_social_cap(monthly_cap, day)
            if code in employee_codes
            else monthly_cap
        )
        deduction = (
            oop
            if code in pension_codes
            and self.l10n_sk_is_agreement()
            and getattr(self, "l10n_sk_agreement_oop", False)
            else 0
        )
        return self.l10n_sk_social_assessment_base(gross, ceiling, deduction)

    def l10n_sk_employee_social_cap(self, cap, day):
        """The employee's maximum assessment base for the month of ``day``.

        § 138 ods. 13 zákona 461/2003 Z. z.: when the employee's insurance
        lasted only part of a calendar month, the base under ods. 9 is adjusted
        by the days for which premiums are paid. The provision names ods. 9
        only, so the employer's cap under ods. 10 is deliberately left whole.
        The result is floored to the eurocent (§ 138 ods. 14).
        """
        self.ensure_one()
        ratio = self.l10n_sk_month_employed_ratio(day)
        if ratio == 1.0:
            return cap
        return float_round(cap * ratio, precision_digits=2, rounding_method="DOWN")

    def l10n_sk_month_employed_ratio(self, day):
        """Share of the calendar month of ``day`` covered by this employment."""
        self.ensure_one()
        days_in_month = monthrange(day.year, day.month)[1]
        first = day.replace(day=1)
        last = day.replace(day=days_in_month)
        start = max(self.contract_date_start or first, first)
        end = min(self.contract_date_end or last, last)
        return min(max((end - start).days + 1, 0) / days_in_month, 1.0)

    def l10n_sk_applies(self, concept):
        """Whether *concept* applies to this contract.

        Called straight from salary-rule conditions::

            result = contract.l10n_sk_applies('SICKNESS_INSURANCE')

        so that the rule states WHICH question it is asking and the answer
        lives in one table, rather than each rule re-deriving it from the
        agreement type and hoping every other rule derived it the same way.
        """
        self.ensure_one()
        return applies(
            concept,
            self.l10n_sk_employment_form(),
            self.l10n_sk_income_is_regular(),
            self.l10n_sk_pension_status(),
        )

    def l10n_sk_employment_form(self):
        """This contract's employment form, defaulting to a pracovný pomer.

        The agreement fields are declared by the country payroll modules, and
        this base depends on neither of them, so they are probed. A database
        with only this module installed has no agreements in it.
        """
        self.ensure_one()
        if "l10n_sk_agreement_type" not in self._fields:
            return EMPLOYMENT
        return self.l10n_sk_agreement_type or EMPLOYMENT

    def l10n_sk_pension_status(self):
        """The pension granted to the worker, or ``False`` for none.

        Declared by the country payroll modules, like the agreement fields,
        and probed for the same reason.
        """
        self.ensure_one()
        if "l10n_sk_pension_type" not in self._fields:
            return False
        return self.l10n_sk_pension_type or False

    def l10n_sk_income_is_regular(self):
        """Whether the remuneration is a regular monthly income.

        A pracovný pomer always is, by definition; the flag is only meaningful
        for agreements.
        """
        self.ensure_one()
        if self.l10n_sk_employment_form() == EMPLOYMENT:
            return True
        if "l10n_sk_income_regular" not in self._fields:
            return True
        return bool(self.l10n_sk_income_regular)

    def l10n_sk_is_agreement(self):
        """Whether this is a dohoda rather than a pracovný pomer."""
        self.ensure_one()
        return self.l10n_sk_employment_form() != EMPLOYMENT
