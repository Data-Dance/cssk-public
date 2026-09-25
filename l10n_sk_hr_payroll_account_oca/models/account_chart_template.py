# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Per-company resolution of the Slovak payroll GL mapping.

The OCA ``payroll_account`` module adds the ``account_debit`` / ``account_credit``
company-dependent fields to ``hr.salary.rule`` and posts a journal entry from
them.  The Slovak salary rules are global (shared across companies) but the
accounts are per company, so we resolve the account *codes* below to the concrete
``account.account`` records of each company once the ``l10n_sk`` chart is loaded.

Sign convention of ``payroll_account`` (see ``hr_payslip.action_payslip_done``):

    * a rule mapped through ``account_debit`` posts a DEBIT when its amount is
      positive and a CREDIT when its amount is negative;
    * a rule mapped through ``account_credit`` posts a CREDIT when positive and a
      DEBIT when negative.

Slovak salary rules keep employee withholdings and the income tax as *negative*
amounts, so they are mapped through ``account_debit`` to land as credits on the
liability accounts (336 / 342).  Employer contributions are positive and get both
sides (524 debit / 336 credit) so each rule is self-balancing.
"""

from odoo import models

# Slovak chart of accounts (l10n_sk) payroll accounts:
#   521000 Mzdové náklady                       -- gross wage expense
#   331000 Zamestnanci                          -- net pay payable
#   336000 Zúčtovanie s orgánmi SP a ZP         -- social + health settlement
#   342000 Ostatné priame dane                  -- income tax withheld
#   524000 Zákonné sociálne poistenie           -- employer contribution expense
#   379000 Iné záväzky                          -- other payables (garnishment...)
#   333000 Ostatné záväzky voči zamestnancom    -- meal payable to employee
#   527000 Zákonné sociálne náklady             -- meal / sick-pay social cost
ACC_WAGE = "521000"
ACC_NET = "331000"
ACC_SOCIAL = "336000"
ACC_TAX = "342000"
ACC_EMPLOYER = "524000"
ACC_OTHER_PAYABLE = "379000"
ACC_MEAL_PAYABLE = "333000"
ACC_SOCIAL_COST = "527000"

_M = "l10n_sk_hr_payroll_oca."

# rule xmlid (without module prefix) -> {"debit": code, "credit": code}
SK_PAYROLL_ACCOUNT_MAPPING = {
    # ---- Gross wage & wage-like náhrady (positive -> debit 521) ------------
    "l10n_sk_hr_payroll_structure_sk_employee_salary_basic_salary_rule": {
        "debit": ACC_WAGE,
    },
    "l10n_sk_holiday_allowance": {"debit": ACC_WAGE},
    "l10n_sk_obstacle_allowance": {"debit": ACC_WAGE},
    "l10n_sk_hr_payroll_structure_sk_employee_salary_reimbursement_salary_rule": {
        "debit": ACC_WAGE,
    },
    # ---- Employee social + health withholdings (negative -> credit 336) ----
    "l10n_sk_sickness_insurance_employee": {"debit": ACC_SOCIAL},
    "l10n_sk_pension_contribution_employee": {"debit": ACC_SOCIAL},
    "l10n_sk_disability_insurance_employee": {"debit": ACC_SOCIAL},
    "l10n_sk_unemployment_insurance_employee": {"debit": ACC_SOCIAL},
    "l10n_sk_health_insurance_employee": {"debit": ACC_SOCIAL},
    "l10n_sk_health_doplatok_employee": {"debit": ACC_SOCIAL},
    # ---- Income tax withheld (negative -> credit 342) ----------------------
    "l10n_sk_income_tax_employee": {"debit": ACC_TAX},
    # ---- Child tax bonus (positive -> debit 342, offsets tax liability) ----
    "l10n_sk_child_bonus": {"debit": ACC_TAX},
    # ---- Employer contributions (positive -> debit 524 / credit 336) -------
    "l10n_sk_sickness_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_pension_contribution_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_disability_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_unemployment_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_short_time_work_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_guarantee_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_accident_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_reserve_fund_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    "l10n_sk_health_insurance_employer": {
        "debit": ACC_EMPLOYER,
        "credit": ACC_SOCIAL,
    },
    # ---- Statutory deductions & garnishment (negative -> credit 379) -------
    "l10n_sk_hr_payroll_structure_sk_employee_salary_attachment_of_salary_rule": {
        "debit": ACC_OTHER_PAYABLE,
    },
    "l10n_sk_hr_payroll_structure_sk_employee_salary_assignment_of_salary_rule": {
        "debit": ACC_OTHER_PAYABLE,
    },
    "l10n_sk_hr_payroll_structure_sk_employee_salary_child_support": {
        "debit": ACC_OTHER_PAYABLE,
    },
    "l10n_sk_hr_payroll_structure_sk_employee_salary_deduction_salary_rule": {
        "debit": ACC_OTHER_PAYABLE,
    },
    "l10n_sk_wage_garnishment": {"debit": ACC_OTHER_PAYABLE},
    # ---- Employer sick-pay náhrada príjmu pri PN (positive -> debit 527) ----
    "l10n_sk_sickness_compensation": {"debit": ACC_SOCIAL_COST},
    # ---- Meal allowance (exempt; employer cost 527 vs payable 333) ---------
    "l10n_sk_meal_voucher_employer": {
        "debit": ACC_SOCIAL_COST,
        "credit": ACC_MEAL_PAYABLE,
    },
    "l10n_sk_meal_voucher_employee": {"debit": ACC_MEAL_PAYABLE},
    # ---- Net salary payable to the employee (positive -> credit 331) -------
    "l10n_sk_hr_payroll_structure_sk_employee_salary_net_salary": {
        "credit": ACC_NET,
    },
    # Intentionally UNMAPPED (informational / totals / stub):
    #   GROSS, TAXBASE, OOP_PENSION, SOCIALEMPLOYEETOTAL,
    #   SOCIALEMPLOYERTOTAL, INCOMETAXTOTAL
}


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _configure_sk_payroll_accounts(self, companies):
        """Resolve the SK payroll account codes to each company's accounts.

        ``account_debit`` / ``account_credit`` are ``company_dependent`` fields,
        so writing them under ``with_company(company)`` stores a per-company
        value on the global salary rules.
        """
        Rule = self.env["hr.salary.rule"]
        Account = self.env["account.account"]
        for company in companies:
            account_by_code = {}

            def _account(code, _company=company):
                if code not in account_by_code:
                    account_by_code[code] = (
                        Account.with_company(_company)
                        .search([("code", "=", code)], limit=1)
                    )
                return account_by_code[code]

            for xmlid, sides in SK_PAYROLL_ACCOUNT_MAPPING.items():
                rule = self.env.ref(_M + xmlid, raise_if_not_found=False)
                if not rule:
                    continue
                vals = {}
                debit = sides.get("debit")
                credit = sides.get("credit")
                if debit and _account(debit):
                    vals["account_debit"] = _account(debit).id
                if credit and _account(credit):
                    vals["account_credit"] = _account(credit).id
                if vals:
                    rule.with_company(company).write(vals)

    def _load(self, template_code, company, install_demo, force_create=True):
        res = super()._load(
            template_code, company, install_demo, force_create=force_create
        )
        # Only for the Slovak chart, and only once the SK salary rules exist.
        if template_code == "sk" and self.env.ref(
            _M + "hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        ):
            self._configure_sk_payroll_accounts(company)
        return res
