19.0.1.2.0 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~~

* Statutory annual-leave (dovolenka) accrual plans (4/5/8 týždňov = 20/25/40
  dní; Zákonník práce §103) attached to the SK holiday leave type, accruing in
  days at 1/12 per whole calendar month (§101 pomerná časť) with a yearly cap
  and carryover (§113). New demo start-of-year 20-day allocation. The 33+/child
  eligibility (§103 ods. 2) and §105 "za odpracované dni" stay manual.

19.0.1.1.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Annual tax reconciliation (ročné zúčtovanie preddavkov na daň, §38 zákona
  č. 595/2003 Z. z.). A new ``l10n.sk.tax.reconciliation`` record per (employee,
  tax year) gathers the year's monthly tax bases, income-tax advances and child
  bonus paid, then recomputes the annual liability with the annual NČZD na
  daňovníka (high-income taper), the annual progressive bands, NČZD na manželku,
  DDS/III. pilier contributions (capped at 180 €) and the annual child-bonus
  entitlement, producing a preplatok or nedoplatok posted onto the
  reconciliation-month payslip through the input-driven ``ANNUAL_TAX_SETTLEMENT``
  salary rule. Ordinary monthly payslips are unaffected. The health-insurance
  reconciliation is insurer-side and excluded.

19.0.1.0.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Port to Odoo 19.0. A contract is now an ``hr.version`` record: the Slovak
  payroll fields move from ``hr.contract`` to ``hr.version`` (whitelisted for
  copy-from-template), the employee mirrors become delegated (``inherited``)
  related fields via ``version_id``, and the form view retargets to the contract
  template (``hr.version``) form. Salary rules, the dated ``hr.rule.parameter``
  mechanism and the absence/leave integration are unchanged.

18.0.2.1.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Absence → payroll integration keyed on stable payroll codes. A new
  ``hr.leave.type.l10n_sk_payroll_code`` (DOVOLENKA / PN / OCR / NEPLATENE /
  OBSTACLE) maps each time-off type to a payroll code; the engine's
  ``_compute_leave_days`` is overridden to key the worked-day line on it. Starter
  leave types are shipped. Any absence now cuts the worked days, so BASIC
  prorates down for it.
* Average earnings (priemerný hodinový zárobok, §134 Zákonníka práce):
  ``payslip.l10n_sk_average_hourly_earnings()`` computes gross wage in the
  previous calendar quarter (less náhrady) ÷ hours worked, with the probable
  earnings (pravdepodobný zárobok) fallback and the minimum-wage floor
  (``l10n_sk_min_hourly_wage``, dated).
* Holiday náhrada (``DOVOLENKA_NAHRADA``) and paid-obstacle náhrada
  (``OBSTACLE_NAHRADA``): hours × priemerný zárobok, added to GROSS (insurable +
  taxable) so a holiday causes no net proration cut.
* Sickness compensation now takes its sick days from the PN leave, keeping the
  ``PN_DAYS`` input as a fallback (``PN_DVZ`` still supplies the DVZ).

18.0.2.0.2 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Partial-month proration of the basic wage: a mid-month hire or leaver now has
  BASIC prorated by worked / scheduled working days (a full month is unchanged).
* Wage garnishment (exekučné zrážky) with the non-seizable amount (nezabaviteľná
  suma): input-driven deduction (``GARNISHMENT`` ordinary 1/3,
  ``GARNISHMENT_PRIORITY`` priority 2/3) computed on the net wage, with dated
  parameters for životné minimum, the 140% basic coefficient, the 25%
  per-dependant coefficient and the 3× unlimited-seizure threshold; new
  ``l10n_sk_garnishment_dependents`` contract field.
* Sickness compensation (náhrada príjmu pri PN): input-driven employer-paid sick
  pay (``PN_DAYS`` + ``PN_DVZ``), days 1–3 at 25% and days 4–10/14 at 55% of the
  capped DVZ, with the 2025→2026 extension from 10 to 14 employer-paid days as a
  dated parameter.

18.0.2.0.1 (2026-07-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* Added the health-insurance OOP (odvodová odpočítateľná položka na zdravotné
  poistenie): max 380 €/mo, phased out to 0 at 570 €, reducing only the
  employee's health assessment base for a regular employment relationship, when
  claimed (new ``l10n_sk_health_oop_claim`` field, dated parameters).
* Implemented the agreements (dohody) DoVP / DoPČ contribution treatment: DoVP is
  charged as irregular income (no sickness / unemployment / short-time-work
  financing), DoPČ as regular income; added the pension odvodová odpočítateľná
  položka (200 €/mo) reducing the old-age, disability and reserve-fund base for
  eligible pensioners/students.

18.0.2.0.0 (2026-07-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* Income tax is computed on the correct tax base
  (gross − employee social − employee health − NČZD) instead of on the raw
  gross.
* Non-taxable part per taxpayer (NČZD) applied, gated by the signed taxpayer's
  declaration, with the high-income taper.
* Health insurance rates and the maximum social assessment base moved to dated
  rule parameters with current values (2025 and 2026).
* Added the child tax bonus (daňový bonus na dieťa) with per-child amounts,
  the percentage-of-tax-base caps and the high-income taper.
* Added ZŤP (disability) handling with the halved health rate and the health
  minimum-base top-up (doplatok).
* Progressive income-tax band table with dated values.
* Meal allowance reworked into meal-voucher and financial-contribution options
  with the statutory minimum employer contribution.
* All statutory rates and ceilings parameterised as dated values.

18.0.1.0.0
~~~~~~~~~~

* Initial Slovak payroll structure, categories and salary rules on the
  ``payroll`` engine.
