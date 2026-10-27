---
title: Czech Payroll — Accounting (OCA)
summary: Posts Czech payslips of the OCA payroll app to the Czech chart of accounts.
verified: 19.0.1.1.1
family: l10n_cz_hr_payroll_base#accounting
---

Sets accounts of the Czech chart on the Czech salary rules — 521 gross pay and sick pay, 524 employer insurance less the employer's social insurance discount, 527 meal allowance, 331 net pay, 336 social and health insurance, 342 income tax less the child tax bonus and the annual tax settlement paid out, 379 garnishments and other deductions, 333 reimbursements — with a debit and a credit account on every rule, so a validated payslip posts a balanced entry. It also creates a general journal *Salaries* (code `SLR`); choose it as the **Salary Journal** on the contract.

Install it on purpose; it needs the OCA `payroll_account` module and the Czech payroll. The accounts are set at installation for the companies already on the Czech chart, and for any company when it loads the Czech chart later.
