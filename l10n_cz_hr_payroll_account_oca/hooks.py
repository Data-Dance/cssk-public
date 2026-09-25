# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

# xmlid (in l10n_cz_hr_payroll_oca) -> (debit account code, credit account code)
#
# Every money-moving rule is mapped with BOTH a debit and a credit account so
# each rule posts a self-balancing pair and the whole payslip move is always
# balanced. Deduction rules carry a negative total: the OCA payslip posts the
# debit account on the credit side and the credit account on the debit side,
# so a deduction mapped debit=336/credit=331 ends up DEBIT 331 / CREDIT 336.
#
#   521 Mzdové náklady          524 Zákonné sociální pojištění
#   527 Zákonné sociální náklady 331 Zaměstnanci
#   336 Zúčtování s institucemi  342 Ostatní přímé daně
#   333 Ostatní závazky vůči zam. 379 Jiné závazky
RULE_ACCOUNT_MAP = {
    "cz_gross_salary_rule": ("521", "331"),
    "cz_sick_nahrada_rule": ("521", "331"),
    "cz_meal_allowance_rule": ("527", "331"),
    "cz_social_ee_rule": ("336", "331"),
    "cz_health_ee_rule": ("336", "331"),
    "cz_income_tax_rule": ("342", "331"),
    "cz_wh_tax_rule": ("342", "331"),
    "cz_tax_credit_rule": ("342", "331"),
    "cz_child_benefit_rule": ("342", "331"),
    "cz_social_er_rule": ("524", "336"),
    "cz_health_er_rule": ("524", "336"),
    "cz_deduction_rule": ("379", "331"),
    "cz_attachment_of_salary_rule": ("379", "331"),
    "cz_assignment_of_salary_rule": ("379", "331"),
    "cz_child_support_rule": ("379", "331"),
    "cz_garnishment_rule": ("379", "331"),
    "cz_reimbursement_rule": ("333", "331"),
}

JOURNAL_CODE = "SLR"


def _configure_cz_payroll_accounts(env, companies=None):
    """Resolve the CZ account codes to each company's accounts and store them
    on the (company-dependent) debit/credit fields of the CZ salary rules.

    Runs only for companies that actually have the l10n_cz chart installed
    (detected by the presence of account 331). Also ensures a general
    "Salaries" journal exists per such company for convenience.
    """
    if companies is None:
        companies = env["res.company"].search([])

    codes = sorted({c for pair in RULE_ACCOUNT_MAP.values() for c in pair})
    Account = env["account.account"]
    Journal = env["account.journal"]

    for company in companies:
        account_by_code = {}
        for code in codes:
            account_by_code[code] = Account.with_company(company).search(
                [
                    *Account._check_company_domain(company),
                    ("code", "=like", "%s%%" % code),
                ],
                limit=1,
            )
        if not account_by_code.get("331"):
            # l10n_cz chart not installed for this company.
            continue

        journal = Journal.with_company(company).search(
            [("code", "=", JOURNAL_CODE), ("company_id", "=", company.id)], limit=1
        )
        if not journal:
            journal = Journal.create(
                {
                    "name": "Salaries",
                    "code": JOURNAL_CODE,
                    "type": "general",
                    "company_id": company.id,
                    "default_account_id": account_by_code["331"].id,
                }
            )

        for xmlid, (debit_code, credit_code) in RULE_ACCOUNT_MAP.items():
            rule = env.ref(
                "l10n_cz_hr_payroll_oca.%s" % xmlid, raise_if_not_found=False
            )
            if not rule:
                continue
            vals = {}
            if account_by_code.get(debit_code):
                vals["account_debit"] = account_by_code[debit_code].id
            if account_by_code.get(credit_code):
                vals["account_credit"] = account_by_code[credit_code].id
            if vals:
                rule.with_company(company).write(vals)
        _logger.info("Configured CZ payroll accounts for company %s", company.name)


def post_init_hook(env):
    _configure_cz_payroll_accounts(env)
