======================
Czech Republic - Payroll
======================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Czech payroll rules for the ``payroll`` engine. This module implements the
monthly payslip for standard employment (pracovní poměr) according to Czech
legislation, including social and health insurance, the income-tax advance and
the child tax benefit/bonus.

The statutory figures are taken from Czech primary sources (ČSSZ, Finanční
správa, MPSV, health insurers) and documented, with the effective dates and
source URLs, in ``docs/cz_payroll_legal.md``.

.. contents::
   :local:

Features
========

* Monthly salary structure *Czech Republic: Regular Pay* (``CZMONTHLY``).
* **Social insurance** — employee 7.1 % (6.5 % pension + 0.6 % sickness) and
  employer 24.8 %, with the maximum annual assessment base (48× průměrná mzda,
  tracked year-to-date).
* **Health insurance** — employee 4.5 % / employer 9 %, with the minimum
  assessment base (= minimum wage) top-up borne by the employee and a skip for
  state-insured persons.
* **Income-tax advance** — 15 % / 23 % two-band on the gross tax base (superhrubá
  mzda abolished), the 23 % band above the monthly threshold (3× průměrná mzda),
  the base rounded up to whole 100 Kč.
* **Tax credits** — sleva na poplatníka, ZTP/P, invalidita.
* **Child tax benefit / bonus** — daňové zvýhodnění by child tier (1st / 2nd /
  3rd+); the surplus over the tax is paid as the daňový bonus.
* **Meal allowance** — stravenkový paušál tax-exempt limit.
* All statutory rates and thresholds are stored as **dated rule parameters**
  (``hr.rule.parameter`` / ``hr.rule.parameter.value``) for 2025 and 2026;
  ``payslip.rule_parameter(code)`` resolves the value effective at the payslip
  date.

Salary rules
============

``BASIC`` → ``MEAL`` → ``GROSS`` → ``SOCIALEE`` / ``SOCIALER`` →
``HEALTHEE`` / ``HEALTHER`` → ``TAXBASE`` → ``INCOMETAX`` → ``TAXCREDIT`` →
``CHILDBEN`` / ``CHILDBONUS`` → statutory deductions → ``NET`` → reporting
totals → ``EMPLOYERCOST``.

Configuration
=============

Per employee/contract (under the *Payroll* access group):

* **Taxpayer Declaration signed (prohlášení poplatníka)** — enables the monthly
  tax credits and the child tax benefit for this employer.
* **Children (tier 1 / 2 / 3+, ZTP/P)** — counts for daňové zvýhodnění.
* **ZTP/P**, **Invalidity degree** — drive the corresponding tax credits.
* **State-insured** — skips the health minimum-base top-up.
* **Meal Allowance / Shift** — the stravenkový paušál amount.

Known issues / Roadmap
======================

Fields/parameters are present, but the following are not fully implemented (the
payslip is computed as regular monthly employment):

* Agreements (dohody) DPP / DPČ, the notified-agreement (oznámená dohoda) regime
  and the insurance thresholds.
* Sickness compensation (náhrada mzdy for the first 14 days) and the reduction
  bands (redukční hranice).
* Wage attachments / insolvency deductions (exekuce/srážky) with the
  nezabavitelná částka.
* Statutory reports (výkazy, ELDP) and the annual reconciliation.
* Worked-days proration of the basic wage for partial months.

Verify the statutory figures against current law before production use.

Credits
=======

Authors
~~~~~~~

* Data Dance s.r.o.
* Odoo Community Association (OCA)

Maintainers
~~~~~~~~~~~

This module is maintained by Data Dance s.r.o.
