# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The net wage a wage garnishment is computed from.

§ 69 ods. 1 Exekučného poriadku (zákon 233/1995 Z. z.): the net wage is the
wage less the advance on income tax and the premiums of the employee. § 89
ods. 1 applies the deductions to income that replaces the remuneration for
work as well, the employer's sick pay among it.

The child tax bonus is no term of it. § 118 ods. 2 Zákonníka práce says the
daňový bonus is not wage, so the advance deducted is the one before the
bonus and the bonus is paid on top in full. Nor are the meal contribution, a
reimbursement of costs (§ 69 ods. 2) or the result of the annual tax
settlement.
"""

#: Salary-rule categories whose lines make up the net wage, the same codes on
#: both payroll engines: the wage with the wage compensations (GROSS), the
#: employee's social and health premiums with the health minimum top-up
#: (SOCIALEMPLOYEE, negative), the tax advance before the child bonus
#: (INCOMETAX, negative) and the employer's sick pay (SICKCOMP).
NET_WAGE_CATEGORIES = ("GROSS", "SOCIALEMPLOYEE", "INCOMETAX", "SICKCOMP")


def garnishment_net_wage(category_totals):
    """Net wage for deductions from ``{category code: total of its lines}``.

    The totals carry the payslip's signs: premiums and tax are negative.
    """
    return round(
        sum(category_totals.get(code) or 0.0 for code in NET_WAGE_CATEGORIES), 2
    )
