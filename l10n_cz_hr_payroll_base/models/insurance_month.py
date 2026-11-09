# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One person's agreements with one employer in one month.

§ 7a odst. 3 of Act 187/2006 Sb. adds up the income from several DPPs with the
same employer, § 7 odst. 4 several small-scale employments, and the sum decides
whether the person is insured. Concurrent agreements are usually separate
employee records, so the person is the record or its birth number.

Shared by the OCA and Enterprise payslips, which differ only in the name of
the field holding the contract.
"""

from dateutil.relativedelta import relativedelta

from odoo import _
from odoo.exceptions import UserError

AGGREGATED_AGREEMENTS = ("dpp", "dpc")


def _digits(number):
    """A birth number is written with or without its slash."""
    return "".join(ch for ch in number or "" if ch.isdigit())


def _person(slip):
    employee = slip.employee_id
    number = _digits(employee.sudo().identification_id)
    if not number:
        return employee
    same = employee.sudo().search([
        ("company_id", "=", slip.company_id.id),
        ("identification_id", "!=", False),
    ]).filtered(lambda e: _digits(e.identification_id) == number)
    return employee | same.with_env(employee.env)


def month_slips(slip, contract_field):
    """The other live payslips of this person and agreement kind this month."""
    kind = slip[contract_field].l10n_cz_agreement_type
    month_start = slip.date_from.replace(day=1)
    month_end = month_start + relativedelta(months=1, days=-1)
    others = slip.env["hr.payslip"].sudo().search([
        ("id", "not in", slip.ids),
        ("employee_id", "in", _person(slip).ids),
        ("company_id", "=", slip.company_id.id),
        ("date_from", "<=", month_end),
        ("date_to", ">=", month_start),
        ("state", "!=", "cancel"),
    ])
    return others.filtered(
        lambda other: other[contract_field].l10n_cz_agreement_type == kind)


def _line_total(slip, code):
    return sum(slip.line_ids.filtered(lambda l: l.code == code).mapped("total"))


def month_income(slip, gross, contract_field):
    """``gross`` plus the same person's other income under this kind."""
    if slip[contract_field].l10n_cz_agreement_type not in AGGREGATED_AGREEMENTS:
        return gross
    return gross + sum(
        _line_total(other, "GROSS")
        for other in month_slips(slip, contract_field))


def check_month(slips, contract_field, threshold):
    """Refuse a confirmation that leaves a payslip on the wrong side of the limit.

    A later agreement can lift a month over the limit after an earlier payslip
    was computed or confirmed; that payslip is then wrong, and correcting it is
    a decision for the payroll accountant.
    """
    for slip in slips:
        kind = slip[contract_field].l10n_cz_agreement_type
        if (slip.company_id.country_id.code != "CZ"
                or kind not in AGGREGATED_AGREEMENTS):
            continue
        group = slip | month_slips(slip, contract_field)
        # A refund nets the month against a payslip that was right when it was
        # confirmed; there is nothing to recompute.
        if any(group.mapped("credit_note")):
            continue
        total = sum(_line_total(member, "GROSS") for member in group)
        insured = total >= threshold(slip, kind)
        wrong = group.filtered(
            lambda member: _line_total(member, "GROSS")
            and bool(_line_total(member, "SOCIALEE")) != insured)
        if wrong:
            raise UserError(_(
                "The agreements of %(employee)s add up to %(total).2f this "
                "month, so these payslips must be recomputed or corrected "
                "before confirming: %(payslips)s",
                employee=slip.employee_id.name, total=total,
                payslips=", ".join(wrong.mapped("name")),
            ))
