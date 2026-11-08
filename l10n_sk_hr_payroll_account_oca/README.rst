==========================================
Slovakia - Payroll with Accounting (OCA)
==========================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Post Slovak payslips to the general ledger**

This module posts Slovak payslips to the general ledger. It sets the
``account_debit`` / ``account_credit`` accounts (from OCA ``payroll_account``)
on the Slovak salary rules of ``l10n_sk_hr_payroll_oca``, mapping them to the
Slovak chart of accounts (``l10n_sk``):

* 521 Mzdové náklady – gross wage (debit)
* 331 Zamestnanci – net pay (credit)
* 336 Zúčtovanie s orgánmi SP a ZP – employee social + health and the employer
  contribution counterpart (credit)
* 342 Ostatné priame dane – income tax withheld (credit) and the child tax bonus
* 524 Zákonné sociálne poistenie – employer contribution expense (debit)

The salary rules are global while the accounts are per company, so the codes are
resolved to each company's accounts when the ``l10n_sk`` chart is loaded (and via
a post-init hook for companies that already had the chart installed).

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_account_oca``
- **Version:** 18.0.1.0.1
- **Licence:** AGPL-3
- **Requires:** ``payroll_account``, ``l10n_sk``, ``l10n_sk_hr_payroll_oca``

Authors: Data Dance s.r.o., Odoo Community Association (OCA)
