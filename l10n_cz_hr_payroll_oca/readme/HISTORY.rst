19.0.1.2.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Employer social-insurance discount (sleva na pojistném, §7a zák. 589/1992):
  a new ``l10n_cz_social_discount_category`` eligibility field and a
  ``SOCIAL_DISCOUNT`` salary rule that books −5 % of the monthly assessment base
  (capped at 1.5× the average wage) for an eligible part-time employee
  (8–30 h/week; under-21 exempt), reducing the employer cost without touching
  the gross social premium. Full-time employees with no category are unaffected.

19.0.1.1.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Annual tax reconciliation (roční zúčtování záloh na daň, §38ch/§38ča ZDP):

  * New ``hr.payroll.cz.annual.tax.recon`` model, one record per (employee, tax
    year). It aggregates the year's done payslips (Σ TAXBASE, Σ INCOMETAX,
    Σ TAXCREDIT, Σ CHILDBEN, Σ CHILDBONUS) and computes the annual tax base
    (Σ gross minus the §15 non-taxable parts, rounded down to whole 100 Kč), the
    annual tax (15 % / 23 % above 36× průměrná mzda), the §35ba credits and the
    §35c child benefit and annual daňový bonus.
  * The §15 non-taxable parts are annual inputs: pension/life contributions
    (joint 48 000 cap), mortgage interest (150 000 cap), gifts (30 % of the base)
    and — recorded but no longer deductible from 2024 — union dues and
    further-education exams.
  * The result is the přeplatek (refund, the common case) plus the doplatek na
    daňovém bonusu; a nedoplatek is not collected through the reconciliation.
  * The settlement is posted onto a payslip (usually the March slip) via the new
    input-driven ANNUAL_TAX_SETTLEMENT salary rule (ALW), which lifts net pay.
    Standard monthly payslips (no reconciliation input) are unchanged.

19.0.1.0.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Initial port to Odoo 19.0. Functionally identical to 18.0.1.0.4. The payroll
  engine moved from ``hr.contract`` to ``hr.version``, so the Czech payroll
  fields now live on ``hr.version`` (whitelisted for template propagation), the
  ``hr.employee`` mirrors are ``inherited`` related fields via ``version_id``,
  and the form view extends the ``hr.version`` contract-template form. The
  salary-rule Python, the dated ``hr.rule.parameter`` mechanism (still shipped
  by this module, as the OCA 19.0 engine provides none) and the absence/leave
  integration are unchanged.

18.0.1.0.4 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* Absence → payroll integration and a real average-earnings mechanism:

  * CZ absence taxonomy mapped to stable payroll codes (CZHOLIDAY, CZSICK,
    CZOCR, CZUNPAID, CZOBSTACLE) via a ``l10n_cz_payroll_code`` on the leave
    type; ``hr.payslip._compute_leave_days`` is overridden to key the
    leave-derived worked-day lines by that code. Each absence prorates the basic
    wage (BASIC) down (``l10n_cz_worked_ratio`` subtracts absence hours). The
    codes map 1:1 onto Odoo master's unified Time Type (see
    docs/master_work_entry_analysis.md).
  * Average hourly earnings (průměrný hodinový výdělek, §351–362 zákoníku práce):
    computed from the previous calendar quarter's counted gross ÷ hours worked,
    floored at the minimum-wage hourly rate (§357), with a probable-earnings
    fallback (§355). The manual ``l10n_cz_avg_hourly_earnings`` field is kept as
    an override. Exposed to the salary rules via
    ``payslip.l10n_cz_average_hourly_earnings()``.
  * Holiday pay (náhrada mzdy za dovolenou, §222) and paid-obstacle pay
    (návštěva lékaře / doprovod, §199 + NV 590/2006) at the full average
    earnings, added into the insurable + taxable GROSS.
  * Sickness compensation (SICKNAHRADA) is now driven from the sickness leave
    (CZSICK); the manual SICK_HOURS input is kept as a fallback.
  * OČR and unpaid leave get no employer pay; unpaid leave prorates BASIC down
    and triggers the health minimum-base top-up. Home office = worked time.
  * Existing standard / dohody / garnishment / sickness-input behaviour is
    unchanged; a full worked month is identical.

18.0.1.0.3 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~

* P3 payroll features:

  * Worked-days proration of the basic wage for partial months: BASIC is now
    prorated by worked/scheduled time so mid-month hires and leavers are paid
    pro rata (a full month is unchanged).
  * Wage garnishment (exekuční srážky ze mzdy) with the 2026 nezabavitelná
    částka (85 % of the sum of the individual living minimum, normative rent and
    energy flat), +1/4 per dependent, the 1.9x unlimited-seizure limit and the
    thirds split for priority (přednostní) vs non-priority (nepřednostní) claims.
    Input-driven via the GARNISHMENT_PREF / GARNISHMENT_NONPREF payslip inputs.
  * Sickness compensation (náhrada mzdy) for the first 14 calendar days: 60 % of
    the average hourly earnings reduced by the hourly redukční hranice (90/60/30
    bands). Input-driven via the SICK_HOURS payslip input.

18.0.1.0.1 (2026-07-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* Agreements (dohody): DPP and DPČ insurance thresholds and taxation. Below the
  rozhodný příjem (notified DPP 25 % of the average wage; non-notified DPP / DPČ
  the general threshold) no social or health insurance is charged and, without a
  signed taxpayer declaration, the income is taxed by the 15 % final withholding
  tax (srážková daň) instead of the advance. Standard employment is unchanged.

18.0.1.0.0 (2026-07-04)
~~~~~~~~~~~~~~~~~~~~~~~~

* Initial release: Czech monthly payroll for standard employment on the
  ``payroll`` engine.
* Social insurance (employee 7.1 % / employer 24.8 %) with the 48× annual
  assessment-base cap tracked year-to-date.
* Health insurance (4.5 % / 9 %) with the minimum-base top-up and the
  state-insured skip.
* Income-tax advance (15 % / 23 %) on the gross tax base, with the monthly
  23 % threshold and the round-up-to-100 base.
* Tax credits (sleva na poplatníka, ZTP/P, invalidita) and the child tax
  benefit / daňový bonus by tier.
* Meal allowance (stravenkový paušál) tax-exempt limit.
* All statutory rates and thresholds parameterised as dated values for 2025
  and 2026, via a lightweight ``hr.rule.parameter`` mechanism.
