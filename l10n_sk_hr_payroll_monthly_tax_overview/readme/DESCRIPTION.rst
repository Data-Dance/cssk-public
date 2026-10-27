Monthly Slovak **Prehľad o zrazených a odvedených preddavkoch na daň** — the
income-tax overview filed to the Finančná správa (tax administrator) each month
under § 39 ods. 9 zákona 595/2003 Z. z.

It is employer-aggregate only (no per-employee annex): every figure is a
company-level sum over the reporting month's payslips. The exported XML (root
``dokument``) is validated against the shipped official ``prehlad2026.xsd``
(PREHLAD_2026).

Line mapping (I. časť — preddavky na daň): r00 ← Σ ``GROSS`` (úhrn zdaniteľných
príjmov), r01/suma ← the withheld income-tax advance before the daňový bonus
(``INCOMETAX19`` + ``INCOMETAX25`` on the hr_payroll engine, a single
``INCOMETAX`` line on the ``payroll`` engine), r04 = r01, r05 ← Σ
``CHILD_BONUS`` (daňový bonus § 33, capped at r04), r08 = r04 − r05 (odvodová
povinnosť). II. časť rekapitulácia (rA/rB/rC) recaps the § 33 bonus.

Lines with no monthly rule source — r02/r03 (ročné zúčtovanie corrections),
r06 (zamestnanecká prémia), r07 and rD/rE/rF (§ 33a daňový bonus na zaplatené
úroky), and the III. časť žiadosti other than the § 33 bonus — are left empty
/ zero and must be filled by hand when applicable.

III. časť: in the overview for the last month of a calendar quarter, the
opt-in *Request refund of the child tax bonus difference* files the žiadosť o
poukázanie rozdielu daňového bonusu with Σ rC over the quarter's three months.

Engine-neutral: it reads payslips through the shared
``l10n_cssk_payroll_declaration_base`` adapter and works on both the
``payroll`` engine and the ``hr_payroll`` engine. Set the company **DIČ**
(10-digit tax identification number) before generating.
