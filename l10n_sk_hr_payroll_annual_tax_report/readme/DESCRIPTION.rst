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
