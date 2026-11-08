================================================
Slovakia — Annual tax reconciliation statement
================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Annual Slovak employer income-tax report (§ 39 ods. 9) for the Finančná správa — aggregate wrap-up + full per-employee annex (Part V), XML validated against the official rh2023 schema. Engine-neutral (payroll or the hr_payroll engine).**

This module generates the annual Slovak employer income-tax report **Hlásenie o
vyúčtovaní dane a o úhrne príjmov zo závislej činnosti, o zrazených preddavkoch
na daň, o zamestnaneckej prémii, o daňovom bonuse a o daňovom bonuse na
zaplatené úroky** (§ 39 ods. 9 zákona č. 595/2003 Z. z.), filed to the Finančná
správa by the end of the fourth month after the tax year end.

It is the annual counterpart of the monthly *Prehľad*: it reuses the same
income-tax rule derivations but aggregates over the whole calendar year and adds
a full per-employee annex (Časť V), one row per employee with the year's income,
withheld tax advances and daňový bonus.

The report is engine-neutral — it reads payslips through the common
``hr.payslip`` API shared by the ``payroll`` engine and the ``hr_payroll``
engine — and validates its XML against the official ``rh2023.xsd`` schema before
it can be marked submitted.

**Verify before filing.** The exact column semantics of Časť V and the II./III.
časť aggregate lines should be confirmed against the current official poučenie
for your tax year; lines without an Odoo rule source (zamestnanecká prémia,
daňový bonus na zaplatené úroky) are emitted empty.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_annual_tax_report``
- **Version:** 18.0.1.1.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_cssk_payroll_declaration_base``

Authors: Data Dance s.r.o.
