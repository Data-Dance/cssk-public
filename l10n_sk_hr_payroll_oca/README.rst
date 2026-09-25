=================
Slovakia - Payroll
=================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

Slovak payroll rules for the ``payroll`` engine. This module implements the
monthly payslip for standard employment (pracovný pomer) according to Slovak
legislation, including social and health insurance, income tax and the child
tax bonus.

The statutory figures are taken from Slovak primary sources (Sociálna
poisťovňa, Finančná správa, MPSVR SR, health insurers) and documented, with the
effective dates and source URLs, in ``docs/sk_payroll_legal.md``.

.. contents::
   :local:

Features
========

* Monthly salary structure *Slovakia: Regular Pay* (``SKMONTHLY``).
* **Social insurance** — sickness, old-age pension, disability, unemployment,
  guarantee, accident and reserve fund, split into employee and employer
  shares, capped at the maximum monthly assessment base (accident insurance is
  uncapped).
* **Health insurance** — employee and employer shares, the halved rate for
  persons with a disability (ZŤP), and a top-up (doplatok) to the minimum
  assessment base.
* **Income tax advance** — computed on the correct tax base
  (gross − employee social − employee health − the non-taxable part NČZD), with
  the progressive band table and the high-income taper of the NČZD.
* **Child tax bonus** (daňový bonus na dieťa) — per-child amounts by age tier,
  the percentage-of-tax-base cap by number of children, and the high-income
  taper; may result in a payout.
* **Meal allowance** (stravné) — meal-voucher and financial-contribution
  options with the statutory minimum employer contribution.
* All statutory rates and ceilings are stored as **dated rule parameters**
  (``hr.rule.parameter`` / ``hr.rule.parameter.value``), so the 2025 ↔ 2026
  differences are data, not code. ``payslip.rule_parameter(code)`` resolves the
  value effective at the payslip date.

Configuration
=============

Per employee/contract (under the *Payroll* access group):

* **Tax Declaration Signed (Vyhlásenie)** — enables the monthly NČZD and the
  child tax bonus for this employer.
* **Children < 15y** / **Children 15–17y** — counts for the child tax bonus.
* **ZŤP / Disabled** — applies the halved health-insurance rate.
* **Meal Allowance Type** and **Meal Days / Month** — drive the meal allowance;
  optional per-day overrides are available.

Known issues / Roadmap
======================

The following are not implemented yet (fields/parameters are present where
noted, but the payslip is computed as regular monthly employment):

* Agreements (dohody) DoVP / DoPČ with the odvodová odpočítateľná položka.
* Sickness benefit / náhrada príjmu and leave (work-entry) integration.
* Monthly and annual statutory reports (výkazy) and the annual reconciliation
  (ročné zúčtovanie).
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
