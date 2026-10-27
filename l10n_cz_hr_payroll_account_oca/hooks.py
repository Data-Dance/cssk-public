# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

# rule CODE (within the CZMONTHLY structure) -> (debit account, credit account)
#
# Keyed by code, resolved against the structure's own rules, so a rule that
# exists without an xmlid (or under another one) is still found, and a code
# that resolves to nothing is reported instead of being skipped in silence —
# which is how CHILDBONUS, ANNUAL_TAX_SETTLEMENT and SOCIAL_DISCOUNT went
# unposted: the employee was paid them, 331 never carried them.
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
    "GROSS": ("521", "331"),
    "SICKNAHRADA": ("521", "331"),
    "MEAL": ("527", "331"),
    "SOCIALEE": ("336", "331"),
    "HEALTHEE": ("336", "331"),
    "INCOMETAX": ("342", "331"),
    "WHTAX": ("342", "331"),
    "TAXCREDIT": ("342", "331"),
    "CHILDBEN": ("342", "331"),
    # Daňový bonus (§ 35d ZDP) and the roční zúčtování přeplatek (§ 38ch) are
    # paid to the employee out of the withheld tax: positive -> DR 342 / CR 331.
    "CHILDBONUS": ("342", "331"),
    "ANNUAL_TAX_SETTLEMENT": ("342", "331"),
    "SOCIALER": ("524", "336"),
    "HEALTHER": ("524", "336"),
    # Sleva na pojistném (§ 7a zák. 589/1992 Sb.) is a negative line that
    # lowers the employer's premium: -> DR 336 / CR 524.
    "SOCIAL_DISCOUNT": ("524", "336"),
    "DEDUCTION": ("379", "331"),
    "ATTACH_SALARY": ("379", "331"),
    "ASSIG_SALARY": ("379", "331"),
    "CHILD_SUPPORT": ("379", "331"),
    "GARNISHMENT": ("379", "331"),
    "REIMBURSEMENT": ("333", "331"),
}

STRUCTURE_XMLID = "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"


def _cz_rules_by_code(env):
    """Map each RULE_ACCOUNT_MAP code to its rule in the CZ structure.

    Returns ``(rules, missing)``: the resolved ``{code: rule}`` and the codes
    that resolved to nothing.
    """
    structure = env.ref(STRUCTURE_XMLID, raise_if_not_found=False)
    rules = {}
    if structure:
        for rule in structure.rule_ids:
            if rule.code in RULE_ACCOUNT_MAP and rule.code not in rules:
                rules[rule.code] = rule
    missing = sorted(set(RULE_ACCOUNT_MAP) - set(rules))
    return rules, missing


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
    rules, missing = _cz_rules_by_code(env)
    if missing:
        _logger.warning(
            "CZ payroll accounts: no rule with code(s) %s in the Czech "
            "structure; those lines will not be posted.", ", ".join(missing))
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

        for rule_code, (debit_code, credit_code) in RULE_ACCOUNT_MAP.items():
            rule = rules.get(rule_code)
            if not rule:
                continue
            vals = {}
            if account_by_code.get(debit_code):
                vals["account_debit"] = account_by_code[debit_code].id
            if account_by_code.get(credit_code):
                vals["account_credit"] = account_by_code[credit_code].id
            if vals:
                # Chart setup is configuration done by an accounting manager, who
                # need not hold payroll rights (OCA payroll grants accounting none).
                rule.sudo().with_company(company).write(vals)
        _logger.info("Configured CZ payroll accounts for company %s", company.name)


def post_init_hook(env):
    _configure_cz_payroll_accounts(env)
