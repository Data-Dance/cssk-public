# SK Payroll — Gap status (stock Enterprise module vs. law vs. our stack)

Baseline: `/home/rex/Odoo/19.0-EE/l10n_sk_hr_payroll/` (Odoo S.A., checkout HEAD
2026-04-23) measured against `sk_payroll_legal.md`.

This started as a TODO list of what the stock module lacks. Nearly all of it has
since been built, so it is now a **status** document with two distinct axes —
conflating them is what made the previous revision misleading:

| Mark | Meaning |
|---|---|
| ✅ | Stock EE lacks it; **we implement it**. Nothing to do. |
| 🟡 | Stock EE lacks it; **we partially implement it**. Real work remaining. |
| ❌ | Stock EE lacks it; **we lack it too**. Real work remaining. |
| ⛔ | Stock EE lacks it; **deliberately out of scope** for us, with a reason. |

Where a module is named without a prefix it lives in this repo. The Slovak
payroll exists in two engine flavours that stay in lockstep —
`l10n_sk_hr_payroll_oca` (OCA `payroll`) and `l10n_sk_hr_payroll_ee` (an overlay
on Enterprise `hr_payroll`) — so "we implement it" means both unless stated.

**State of the stock module, for reference:** 29 salary rules, two structures,
and exactly two rule parameters (`l10n_sk_monthly_taxable_max` = 8477 and
`l10n_sk_income_tax_threshold` = 41445.46, both dated 2017-01-01). Every other
rate is a literal `result_rate = …` inside a rule body. The last commit touching
Slovak content is from 2025-09; everything since is Weblate i18n and generic
cross-localisation fixes.

---

## P1 — Blocking correctness (the stock payslip is wrong today)

- ✅ **Income tax base computed on raw GROSS.**
  *Stock:* `INCOMETAX19`/`INCOMETAX25` apply `result_rate = -19`/`-25` to
  `categories['GROSS']` — contributions are never deducted.
  *Ours:* a real `TAXBASE` rule = `GROSS − |SOCIALEMPLOYEE| − |HEALTH|`, which the
  income-tax rules consume.

- ✅ **Non-taxable part per taxpayer (NČZD) not applied.**
  *Ours:* `l10n_sk_nczd_monthly` (470.54 / 479.48 / 497.23 for 2024/2025/2026),
  gated on `l10n_sk_tax_declaration_signed`.
  *Deviation worth knowing:* the § 11 ods. 2 high-income taper is **not** applied
  to the monthly advance. That is correct per § 35 — the taper is settled in the
  annual reconciliation, which `l10n.sk.tax.reconciliation` does.

- ✅ **Health employer rate 10 %, must be 11 %.**
  *Ours:* `l10n_sk_health_rate_employer` = 11 since 2024-01-01.

- ✅ **Health employee rate must rise 4 % → 5 % for 2026.**
  *Ours:* `l10n_sk_health_rate_employee`, 4 % (2024–25) → 5 % (2026-01-01).

- ✅ **Maximum monthly assessment base stuck at 8477 (2017).**
  *Ours:* `l10n_sk_monthly_taxable_max` = 9128 (2024) / 15730 (2025) / 16764
  (2026). Accident insurance stays un-capped, as it must.

- ✅ **Child tax bonus (daňový bonus na dieťa) entirely missing.**
  *Ours:* `CHILD_BONUS` with the age tiers, the %-of-tax-base caps and the taper
  (`l10n_sk_child_bonus_under_15`, `_15_18`, `_pct_caps`, `_taper_threshold`,
  `_taper_coeff`).

- ✅ **Income-tax threshold stale, 2026 progressive bands missing.**
  *Ours:* `l10n_sk_income_tax_bands`, a dated band table computed on the MONTHLY
  base. 2026 = `[19 %, 3665.28], [25 %, 5029.10], [30 %, 6250.86], [35 %, ∞]`.

---

## P2 — Completeness (legally required, narrower impact)

- ✅ **ZŤP / disabled employee handling.**
  *Ours:* `l10n_sk_ztp` on the version selects
  `l10n_sk_health_rate_employee_ztp` / `_employer_ztp`.

- ✅ **Health minimum base / doplatok (životné minimum).**
  *Ours:* `HEALTHDOPLATOK` (`HEALTH_DOPLATOK` on the `_dd` side) against
  `l10n_sk_health_min_base`.
  *Known ordering caveat (`_dd` only):* the doplatok is charged to the employee
  and sequenced after `TAXBASE`, so it does not reduce the tax base. Only
  material for sub-minimum wages.

- 🟡 **Agreements (dohody) DoVP / DoPČ structures.**
  *Have:* `l10n_sk_agreement_type` on the version, the fund set adjusted per
  agreement kind, and full VPP reporting for dohody
  (`l10n_sk_hr_payroll_vpp`).
  *Missing:* dohody still run through the single `SKMONTHLY` structure. No
  dedicated structure types, and the 350 h/yr and 10 h/wk limits are not
  enforced or warned on. **The largest remaining hole in the stack** — dohodári
  are very common in Slovakia.

- 🟡 **Dohoda OOP for students/pensioners (€200) and seasonal DoPČ OOP (€762).**
  *Have:* the regular €200 OOP (`l10n_sk_dohoda_oop`, `OOP_PENSION` rule).
  *Missing:* `l10n_sk_dohoda_oop_seasonal` (762) is shipped as a parameter but
  no field flags a seasonal agreement, so the regular €200 is always used.
  Case-specific dohodár exemptions for pensioners/students beyond the modelled
  fund set are also not covered.

- ✅ **Meal allowance not computed per law.**
  *Ours:* `MEALEMPLOYER` / `MEALEMPLOYEE` with `l10n_sk_stravne_5_12h`,
  `l10n_sk_meal_employer_pct` (≥55 %) and `l10n_sk_meal_voucher_min_pct`;
  voucher vs. financial contribution selected on the version. Both lines sit in
  dedicated categories outside GROSS, so the amount is excluded from tax and
  from both contribution bases rather than merely netted out.

- ✅ **Statutory reporting / výkazy.**
  *Ours:* seven modules on `l10n_cssk_payroll_declaration_base`, each shipping
  the official XSD and validating its export against it —
  `l10n_sk_hr_payroll_mvp` (MVPP-v2026), `_vpp` (VPP-v2026, dohody), `_health`
  (dávka 514, 514-2023), `_prehlad` (prehlad2026), `_hlasenie` (rh2023, incl.
  the Časť V annex), `_rlfo` (RLZEC-v2026), `_eldp` (ELDP-v2015_1.3).
  *Documentation gap:* none of the seven ships a `readme/ROADMAP.rst`, so their
  own limitations and schema-vintage coverage are undocumented.

- ✅ **Annual reconciliation of income tax** (ročné zúčtovanie preddavkov na daň,
  § 38) — `l10n.sk.tax.reconciliation`, which also settles the NČZD taper and
  the annual child-bonus true-up.

- ⛔ **Ročné zúčtovanie zdravotného poistenia (RZZP).** Performed by the health
  insurer, not the employer. Out of scope by design, not by omission.

---

## P3 — Robustness and completeness

- ✅ **Move all hardcoded rates to dated `hr.rule.parameter` values.**
  *Ours:* 48 dated parameters (`_oca`) / 47 (`_dd`) against the stock module's
  two. This is the single biggest structural difference between the stacks.

- ✅ **Minimum-wage data + validation (levels 1–6).**
  *Ours:* `l10n.sk.minimum.wage` in `l10n_sk_hr_payroll_priplatky` — 2024/2025/
  2026 × six stupne náročnosti, monthly and hourly — plus a `MIN_WAGE_TOPUP`
  rule paying the doplatok to the claim for the contract's level.
  *Note:* monthly-paid and hourly-paid employees are measured against different
  figures on purpose. The published hourly amounts are the monthly amount over
  the statutory 174 hours, so in a month scheduling more (June 2026 schedules
  176) an employee on exactly the monthly minimum falls under the hourly figure
  while owing nothing. Proration divides by FULL-TIME hours, never the
  employee's own schedule.

- ✅ **Wage surcharges (príplatky) — night/weekend/holiday/overtime.**
  *Ours:* `l10n_sk_hr_payroll_priplatky` (+ `_oca` / `_dd` bridges): night
  § 122a, Saturday § 122b, Sunday § 122c, public holiday § 122, overtime § 121
  (pay + uplift), difficult conditions § 123, standby § 96 ods. 5, with the
  risky-work and collective-agreement rate variants.
  *Design note:* driven by payslip inputs, not work-entry types — night/weekend
  hours OVERLAY ordinary working time, so a work-entry type carrying those codes
  would move them out of `WORK100` and prorate BASIC down. A worked-days line of
  the code still wins where a site models it properly.
  *Remaining within the module:* no base pay for public-holiday hours (only the
  uplift); overtime base pay valued at average earnings; no check that a
  collective agreement backs a reduced rate; § 123 is a single rate. See its
  `readme/ROADMAP.rst`.

- ✅ **Attachment/garnishment limits (zrážky zo mzdy).**
  *Ours:* the `l10n_cssk_hr_payroll_garnishment_*` family — full multi-claim
  waterfall, order register, balance tracking, remittance to the bailiff and the
  statutory employer notices, replacing the stock module's raw `ATTACH_SALARY` /
  `CHILD_SUPPORT` inputs.
  *Open legal question:* the SK mixed-class waterfall is a documented modelling
  choice where the statute is silent on how classes with different protected
  bases share the first third. **Still wants a Slovak practitioner's review** —
  the one item in this document carrying genuine legal risk rather than
  incompleteness.

- 🟡 **Employee premium (zamestnanecká prémia).**
  *Have:* an `employee_premium` field on `l10n.sk.tax.reconciliation`, credited
  into the annual settlement.
  *Missing:* the eligibility test and the amount are not computed — the payroll
  officer enters the figure.

- 🟡 **NČZD on spouse (nezdaniteľná časť na manžela/manželku).**
  *Have:* an `nczd_spouse` field on `l10n.sk.tax.reconciliation`, added to the
  annual non-taxable total alongside the tapered taxpayer NČZD and DDS.
  *Missing:* the § 11 ods. 3 amount is not derived from the spouse's own income
  and the high-earner taper is not applied to it — again entered by hand.

*(Also present though never in the original gap list: DDS / third-pillar
contributions, § 11 ods. 8, capped at the annual €180.)*

---

## Not in the original gap list, but open

These surfaced while building and are tracked in the modules' own
`readme/ROADMAP.rst` files:

- ❌ **PN's denný vymeriavací základ is still a payslip input** (`PN_DVZ`). It
  derives from the prior year's assessment base, which is not modelled.
- ❌ **Sickness náhrada (`SICK_COMP`) is not taxed** on the payslip, as a
  documented simplification. In reality it is subject to income tax.
- 🟡 **Priemerný zárobok (§ 134) simplifications:** counted gross is the GROSS
  line less the SK náhrada lines rather than a from-scratch § 118 wage
  classification; only the ≥168-hours branch is exercised, not the ≥21-days
  alternative; the PN náhrada uses the leave's WORKING days as a proxy for the
  statutory CALENDAR-day count of the first 10/14 days.
- 🟡 **`_dd` upgrade fragility:** overriding `amount_python_compute` replaces the
  whole upstream rule body, so every Enterprise upgrade needs a re-check that
  nothing new was dropped and that the overridden XML ids still resolve.
