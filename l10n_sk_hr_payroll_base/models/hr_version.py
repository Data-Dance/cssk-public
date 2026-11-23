# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Expose the applicability table to the salary rules of both engines.

``hr.version`` is core ``hr`` in Odoo 19, and the salary-rule namespace of both
engines hands the version to every rule — as ``contract`` on the OCA engine and
``version`` on Enterprise — so a method here is reachable from a rule condition
on either without this module knowing which engine is installed.
"""

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_DOWN

from dateutil.relativedelta import relativedelta

from odoo import _, api, models
from odoo.exceptions import ValidationError

from ..applicability import EMPLOYMENT, applies

# § 227a ods. 1 zákona 461/2003 Z. z. names the person on maternity, paternity
# or parental leave from this day (the wording in force from 1 January 2027).
OOP_PARENTAL_FROM = date(2027, 1, 1)
OOP_PARENTAL_FORMS = ("dovp", "dopc")


def birth_number_key(identification):
    """The digits of a birth number: the key of a person.

    A birth number is written with or without its slash, so only the digits
    are compared. Without a birth number there is no key and no person to
    match.
    """
    return "".join(ch for ch in (identification or "") if ch.isdigit())


class HrVersion(models.Model):
    _inherit = "hr.version"

    # ------------------------------------------------------------------
    # one declaration of the taxpayer for one employer
    # ------------------------------------------------------------------
    def _l10n_sk_tax_declaration_conflicts(self):
        """The versions of other employee records of the same person and
        company that carry a signed declaration on a day this one does.

        § 36 ods. 6 zákona 595/2003 Z. z.: the employee gives the declaration
        to an employer, and § 35 ods. 1 písm. b) deducts the non-taxable
        amount once from the total the employer pays in the month. Two
        employee records of one person at one employer (an employment and an
        agreement) are one taxpayer at one employer: the box
        ``l10n_sk_tax_declaration_signed``, which each payroll engine defines
        on the version, may be ticked on one of them at a time.

        A person is recognised by the birth number. Records without one, of
        different companies, or whose versions do not share a day, never
        conflict.
        """
        conflicts = self.browse()
        if "l10n_sk_tax_declaration_signed" not in self._fields:
            return conflicts
        for version in self.sudo():
            if not version.l10n_sk_tax_declaration_signed or not version.employee_id:
                continue
            key = birth_number_key(version.identification_id)
            if not key:
                continue
            others = self.sudo().search([
                ("company_id", "=", version.company_id.id),
                ("employee_id", "!=", version.employee_id.id),
                ("employee_id", "!=", False),
                ("l10n_sk_tax_declaration_signed", "=", True),
                ("identification_id", "!=", False),
            ])
            start, end = version.date_start, version.date_end
            for other in others:
                if birth_number_key(other.identification_id) != key:
                    continue
                if end and other.date_start and other.date_start > end:
                    continue
                if other.date_end and start and other.date_end < start:
                    continue
                conflicts |= other
        return conflicts

    @api.constrains("identification_id")
    def _check_l10n_sk_tax_principal_person(self):
        # A birth number changed on a record that is taxed together with
        # another (hr.employee, ``l10n_sk_tax_principal_id``).
        self.employee_id._l10n_sk_check_tax_principal_person()

    def _l10n_sk_tax_declaration_offenders(self):
        """Every pair of versions that breaks the rule, each pair once.

        For the update of a database that holds such data already: the
        constraint is checked when a record is written, never by an update,
        so the update lists the pairs in the log instead.
        """
        if "l10n_sk_tax_declaration_signed" not in self._fields:
            return []
        signed = self.sudo().search([
            ("l10n_sk_tax_declaration_signed", "=", True),
            ("identification_id", "!=", False),
            ("employee_id", "!=", False),
        ])
        pairs = []
        for version in signed:
            for other in version._l10n_sk_tax_declaration_conflicts():
                if version.id < other.id:
                    pairs.append((version, other))
        return pairs

    def _l10n_sk_check_single_tax_declaration(self):
        """Refuse a second signed declaration of one person at one employer.

        Called from the ``@api.constrains`` of each engine, which owns the
        box. The versions of the same employee records are checked with the
        written ones: moving one version's date moves the end of the one
        before it.
        """
        versions = self | self.employee_id.sudo().version_ids
        for version in versions:
            conflict = version._l10n_sk_tax_declaration_conflicts()[:1]
            if conflict:
                raise ValidationError(_(
                    "%(employee)s and %(other)s have the same birth number, so "
                    "they are one taxpayer at this employer. The taxpayer's "
                    "declaration can be signed on one of them at a time "
                    "(§ 36 ods. 6 zákona č. 595/2003 Z. z.), and it is ticked "
                    "on both for a day they share: from %(start)s on "
                    "%(employee)s and from %(other_start)s on %(other)s. "
                    "Untick Tax Declaration Signed on one of the two.",
                    employee=version.employee_id.display_name,
                    other=conflict.employee_id.display_name,
                    start=version.date_start,
                    other_start=conflict.date_start,
                ))

    def l10n_sk_employee_social_cap(self, cap, day):
        """The employee's maximum assessment base for the month of ``day``.

        § 138 ods. 13 zákona 461/2003 Z. z.: when the employee's insurance
        lasted only part of a calendar month, the base under ods. 9 is adjusted
        by the days for which premiums are paid. The provision names ods. 9
        only, so the employer's cap under ods. 10 is deliberately left whole.
        Floor the daily base first (§ 138 ods. 13), then multiply the
        insured days. A full month retains the unadjusted monthly maximum.
        """
        self.ensure_one()
        days_in_month = monthrange(day.year, day.month)[1]
        insured_days = self._l10n_sk_month_employed_days(day)
        if insured_days == days_in_month:
            return cap
        daily = (Decimal(str(cap)) / days_in_month).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN)
        return float(daily * insured_days)

    def l10n_sk_month_employed_ratio(self, day):
        """Share of the calendar month of ``day`` covered by this employment."""
        return self._l10n_sk_month_employed_days(day) / monthrange(day.year, day.month)[1]

    def _l10n_sk_month_employed_days(self, day):
        """Count whole calendar days without recovering them from a float ratio."""
        self.ensure_one()
        days_in_month = monthrange(day.year, day.month)[1]
        first = day.replace(day=1)
        last = day.replace(day=days_in_month)
        start = max(self.contract_date_start or first, first)
        end = min(self.contract_date_end or last, last)
        return min(max((end - start).days + 1, 0), days_in_month)

    def l10n_sk_applies(self, concept):
        """Whether *concept* applies to this contract.

        Called straight from salary-rule conditions::

            result = contract.l10n_sk_applies('SICKNESS_INSURANCE')

        so that the rule states WHICH question it is asking and the answer
        lives in one table, rather than each rule re-deriving it from the
        agreement type and hoping every other rule derived it the same way.
        """
        self.ensure_one()
        return applies(concept, self.l10n_sk_employment_form(),
                       self.l10n_sk_income_is_regular(),
                       self.l10n_sk_pension_status())

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

    def l10n_sk_agreement_oop_applies(self, day):
        """Whether the agreement OOP reduces the bases in the month of ``day``.

        Called from the salary rules of both engines. The claim itself is the
        contract's *OOP Agreement* box; this dates it by § 227a zákona
        461/2003 Z. z.:

        * ods. 3 písm. a): the claim takes effect on the day the relationship
          arises if it was notified (and, on the ground of leave, the leave
          proved) by then, otherwise on the first day of the month after. The
          OOP is an amount per calendar month (§ 138a), so a relationship that
          arises mid-month has it for that month. A claim with NO notice date
          is not dated: it lasts while the box is ticked, as it always did —
          except on the ground of leave, where the date is required.
        * the ground of maternity, paternity or parental leave exists from
          1 January 2027 and on a DoVP or DoPČ only;
        * ods. 4: on that ground the right ends with the month in which the
          person stopped being on leave. The month of the leave's LAST DAY is
          taken as that month, also when the leave ends on the last day of a
          month — the reading that grants fewer months of OOP.

        The end of a claim by the worker's own notice (ods. 3 písm. b)) is
        not a date here: untick the box in a contract version dated the first
        day of the following month. The ground is ignored on a DoBPŠ, whose
        holder has the right without one.
        """
        self.ensure_one()
        if not self.l10n_sk_is_agreement():
            return False
        if "l10n_sk_agreement_oop" not in self._fields:
            return False
        if not self.l10n_sk_agreement_oop:
            return False
        if "l10n_sk_agreement_oop_reason" not in self._fields:
            return True
        parental = (
            self.l10n_sk_agreement_oop_reason == "parental"
            and self.l10n_sk_employment_form() in OOP_PARENTAL_FORMS
        )
        notified = self.l10n_sk_agreement_oop_notified
        if not notified:
            return not parental
        month = day.replace(day=1)
        start = self.contract_date_start
        if start and notified <= start:
            effective = start.replace(day=1)
        else:
            effective = notified.replace(day=1) + relativedelta(months=1)
        if parental:
            effective = max(effective, OOP_PARENTAL_FROM)
        if month < effective:
            return False
        leave_end = parental and self.l10n_sk_agreement_oop_leave_end
        return not leave_end or month <= leave_end.replace(day=1)
