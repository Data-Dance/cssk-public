Statutory reporting is NOT part of this module — it lives in a separate,
engine-neutral family built on ``l10n_cssk_payroll_declaration_base``, each
module shipping the official XSD and validating its export against it:

* ``l10n_cz_hr_payroll_pvpoj`` — monthly Přehled o výši pojistného (ČSSZ),
  validated against ``PVPOJ25.xsd``.
* ``l10n_cz_hr_payroll_onz`` — Oznámení o nástupu do zaměstnání / skončení,
  built from the employee and ``hr.version`` lifecycle
  (``ONZ2022_20230616.xsd``).
* ``l10n_cz_hr_payroll_eldp`` — the annual Evidenční list důchodového
  pojištění (``ELDP09.xsd``).
* ``l10n_cz_hr_payroll_health`` — the monthly Přehled o platbě pojistného
  (PPPZ) and the bulk enrol/terminate notification (HOZ), per health insurer.
* ``l10n_cz_hr_payroll_vyuctovani`` — the annual Vyúčtování daně z příjmů ze
  závislé činnosti for the Finanční správa (EPO ``dpzvd6_epo2.xsd``).

Not implemented anywhere in the stack yet:

* Wage surcharges (příplatky) for přesčas, svátek, noční práce, víkend and
  ztížené pracovní prostředí (§§ 114–118 zákoníku práce), and the zaručená
  mzda groups. The Slovak side has these in
  ``l10n_sk_hr_payroll_priplatky``; the Czech equivalent is not built. The two
  statutes differ in shape — Czech příplatky are percentages of the průměrný
  výdělek rather than of the minimum wage — so the Slovak module cannot simply
  be pointed at CZ.

Simplifications in the implemented P3 features (verify against current law
before production use):

* Absence → payroll: CZ absences are recorded as leaves mapped to stable
  payroll codes and prorate the basic wage down; holiday / paid-obstacle time is
  compensated at the průměrný výdělek. Home office is treated as ordinary worked
  time (no dedicated code). The CZ leave types are created with
  ``requires_allocation`` off (payroll only reads the resulting leave); real
  dovolená allocation/entitlement management is out of scope. Public holidays
  and the exact sickness day-count (only the first 14 calendar days, from the
  first missed shift) are not enforced by the engine — model the sickness leave
  to cover only the compensable shifts.
* Average earnings (průměrný hodinový výdělek, §351–362): the "counted gross" is
  approximated by the BASIC worked-time wage (excludes náhrady, per §356, but
  also excludes taxable bonuses/příplatky that should count); the "21 worked
  days" test is approximated by "any worked hours in the previous quarter"; the
  probable earnings (§355) are derived from the current wage and scheduled hours
  rather than the quarter-to-date earnings. The PHV is recomputed per payslip
  from prior-quarter payslips rather than frozen for the whole quarter.
* Sickness compensation (náhrada mzdy for the first 14 calendar days): 60 % of
  the reduced average hourly earnings with the redukční hranice as dated
  parameters. It is added to the net take-home but is not run through income
  tax: in reality náhrada mzdy is subject to income tax but not to
  social/health insurance.
* Wage garnishment: install ``l10n_cssk_hr_payroll_garnishment_base`` (plus the
  engine bridge) for the full multi-claim § 279/§ 280 waterfall, an order
  register, balance tracking, remittance to the bailiff and the statutory
  employer notices. Without it the rule falls back to a single input-driven
  claim per payslip (priority OR non-priority). Either way the nezabavitelná
  částka uses the 2026 methodology (85 % of the sum of the individual living
  minimum, the normative rent and the energy flat), valid from 2026-01-01.
* Annual tax reconciliation (roční zúčtování záloh na daň, §38ch/§38ča): a
  per-(employee, year) record aggregates the year's payslips (Σ tax base,
  Σ withheld advance, Σ credit, Σ child benefit / bonus) and computes the annual
  tax (15 %/23 % above 36× průměrná mzda), the §35ba credits (poplatník in full,
  manžel/ka, ZTP/P, invalidita) and the §35c child benefit / annual bonus, then
  the přeplatek and the doplatek na daňovém bonusu, posted onto a payslip via the
  ANNUAL_TAX_SETTLEMENT rule. Simplifications: the §15 non-taxable parts are
  manual annual inputs (pension/life jointly capped at 48 000; mortgage interest
  capped at 150 000 — the 300 000 pre-2021 cap is not modelled; gifts capped at
  30 % of the base); union dues and further-education exams are recorded but not
  deducted (repealed from 2024); a nedoplatek is not collected through the
  reconciliation; ZTP/P, invalidity and child counts are read from the current
  version rather than reconstructed month by month. The employee-side health/
  social annual reconciliation is insurer-side and out of scope.
* Employer social-insurance discount (sleva na pojistném, §7a): the discount is
  −5 % of the monthly assessment base (capped at 1.5× the average wage) for an
  eligible part-time employee (weekly hours read from the resource calendar,
  8–30 h/week; under-21 exempt). Simplifications: the per-hour base limit
  (1.15 % of the average wage) and the 138 h/month cap are shipped as dated
  parameters but not enforced by the rule; eligibility (the § 7a category and
  the ``duvodSlevy`` reason letter) is taken from the contract/version field,
  not validated; and the single-employer rule plus the mandatory notification of
  intent to ČSSZ (oznámení úmyslu / OZUSPOJ) are organisational and out of
  scope — the rule assumes this employer is entitled to claim.

Verify the statutory figures against current law before production use.
