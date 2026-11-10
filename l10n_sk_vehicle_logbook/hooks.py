# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Pohľadávky voči zamestnancom: where the Slovak chart books an advance paid
# to an employee until the settlement clears it.
SK_ADVANCE_ACCOUNT_CODE = "335000"


def set_sk_advance_account(env):
    """Point the Employee Advance product at 335000 in every company with
    the Slovak chart, where it has no account yet."""
    product = env.ref("hr_expense_advance_clearing.product_emp_advance", False)
    if not product:
        return
    for company in env["res.company"].search([("chart_template", "=", "sk")]):
        product_c = product.with_company(company)
        if product_c.property_account_expense_id:
            continue
        account = env["account.account"].with_company(company).search([
            *env["account.account"]._check_company_domain(company),
            ("code", "=", SK_ADVANCE_ACCOUNT_CODE),
        ], limit=1)
        if not account:
            continue
        if not account.reconcile:
            account.reconcile = True
        product_c.property_account_expense_id = account


def post_init_hook(env):
    set_sk_advance_account(env)
