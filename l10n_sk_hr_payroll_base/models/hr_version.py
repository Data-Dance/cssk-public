# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Expose the applicability table to the salary rules of both engines.

``hr.version`` is core ``hr`` in Odoo 19, and the salary-rule namespace of both
engines hands the version to every rule — as ``contract`` on the OCA engine and
``version`` on Enterprise — so a method here is reachable from a rule condition
on either without this module knowing which engine is installed.
"""

from calendar import monthrange

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

from ..applicability import EMPLOYMENT, applies
from ..health_assessment import employee_assessment, minimum_assessment


class HrVersion(models.Model):
    _inherit = "hr.version"

    l10n_sk_health_minimum_opt_out = fields.Boolean(
        string="Concurrent-employment minimum opt-out",
        help="Section16a(5): the employee has concurrent employers and has "
        "given a written notice not to apply the minimum top-up here. "
        "This is different from disability or state-insured status.",
    )
    l10n_sk_health_minimum_evidence = fields.Char(
        string="Minimum opt-out notice reference",
        help="Reference to the retained written notice and concurrent-employment facts effective on this version.",
    )

    def l10n_sk_health_minimum_is_opted_out(self):
        self.ensure_one()
        if (
            self.l10n_sk_health_minimum_opt_out
            and not (self.l10n_sk_health_minimum_evidence or "").strip()
        ):
            raise UserError(
                _(
                    "Record the employee's written concurrent-employment minimum opt-out notice before calculation."
                )
            )
        return bool(self.l10n_sk_health_minimum_opt_out)

    @api.model
    def _get_whitelist_fields_from_template(self):
        values = super()._get_whitelist_fields_from_template() or []
        return values + [
            name
            for name in (
                "l10n_sk_health_minimum_opt_out",
                "l10n_sk_health_minimum_evidence",
            )
            if name not in values
        ]

    def l10n_sk_health_employee_assessment(
        self, income, rate, day, maximum, phaseout_end
    ):
        """Canonical source for both payroll and the health declaration.

        This engine-neutral method receives dated parameters from its caller;
        it does not depend on either salary-rule parameter model.
        """
        self.ensure_one()
        employment_ratio = self.l10n_sk_month_employed_ratio(day)
        calendar = self._l10n_sk_health_calendar_context(day)
        if calendar:
            employment_ratio = (
                calendar["op_employment_days"] / calendar["calendar_days"]
            )
        eligible = self.l10n_sk_applies("HEALTH_ALLOWANCE") and employment_ratio > 0
        concurrent = calendar and (
            calendar["concurrent_self_employment"]
            or calendar["concurrent_other_employment"]
        )
        result = employee_assessment(
            income,
            income if eligible else 0,
            claim=bool(
                getattr(self, "l10n_sk_health_oop_claim", False)
                and eligible
                and not concurrent
            ),
            employment_ratio=employment_ratio,
            rate=rate,
            maximum=maximum,
            phaseout_end=phaseout_end,
            exempt=bool(getattr(self, "l10n_sk_health_exempt", False)),
        )
        return {
            key: float(value) if key != "exempt" else value
            for key, value in result.items()
        }

    def _l10n_sk_health_calendar_context(self, day):
        """The effective reviewed month, never a superseded or unfinished revision."""
        self.ensure_one()
        self.check_access("read")
        month = fields.Date.to_date(day).replace(day=1)
        calendar = self.env["l10n.sk.health.calendar"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("employee_id", "=", self.employee_id.id),
                ("month", "=", month),
                ("state", "!=", "superseded"),
            ]
        )
        if calendar and calendar.state != "reviewed":
            raise UserError(
                _("Finish reviewing the employee's health calendar before calculation.")
            )
        return calendar._calendar_context() if calendar else False

    def l10n_sk_health_is_disabled(self, day):
        self.ensure_one()
        calendar = self._l10n_sk_health_calendar_context(day)
        return (
            calendar["disability_in_month"]
            if calendar
            else bool(getattr(self, "l10n_sk_ztp", False))
        )

    def l10n_sk_health_calendar_minimum(
        self, day, base, ee_rate, er_rate, employee, employer
    ):
        calendar = self._l10n_sk_health_calendar_context(day)
        if not calendar:
            return False
        facts = minimum_assessment(
            base,
            ee_rate,
            er_rate,
            0
            if getattr(self, "l10n_sk_health_exempt", False)
            else calendar["minimum_days"],
            calendar["calendar_days"],
            employee,
            employer,
            opt_out=self.l10n_sk_health_minimum_is_opted_out(),
        )
        return {key: float(value) for key, value in facts.items()}

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
