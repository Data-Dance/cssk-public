---
title: Slovak Payroll — Accounting (OCA)
summary: Posts Slovak payslips of the OCA payroll app to the Slovak chart of accounts.
verified: 19.0.1.0.5
family: l10n_sk_hr_payroll_base#accounting
---

Sets the debit and credit accounts of the Slovak salary rules for each company on the Slovak chart — wages, employer-side obstacle pay and (when installed) the wage surcharges on 521000, net pay on 331000, insurance on 336000 and 524000, income tax, the child bonus and the annual tax settlement on 342000, garnishments on 379000, meals and employer sick pay on 527000 and 333000 — so that a validated payslip posts a balanced entry. It does this on installation for companies already on the Slovak chart, and later whenever a company loads it.

Install it on purpose; it needs the OCA `payroll_account` module and the Slovak chart of accounts. Choose the *Salary Journal* on each contract.

These are initial defaults. Once a rule has an account usable by the company, subsequent chart loads preserve its debit/credit pair, including an intentionally empty opposite side. Separate insurer analytics and other accounting choices therefore survive deferred company setup. Newly installed rules without a usable mapping still receive the defaults. Account lookup uses Odoo's native company domain, including permitted parent-company accounts for branches.

To restore the initial defaults, explicitly clear both accounts on the relevant rule and run chart setup again. Existing payroll source protections still apply: clearing configuration is not a way to rewrite posted payroll or its retained evidence.
