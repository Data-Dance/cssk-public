# SK Payroll — Gap TODO (EE module vs. law)

Gaps between `/home/rex/Odoo/19.0-EE/l10n_sk_hr_payroll/` and `sk_payroll_legal.md`.
Grouped by priority. Each item: **what's missing · why it matters · implementation hint**.

---

## P1 — Blocking correctness (payslip is wrong today)

- [ ] **Income tax base is computed on raw GROSS.**
  *Why:* Slovak tax base = gross − employee social (9.4%) − employee health (5%/4%) − NČZD.
  Taxing gross over-states tax on every payslip.
  *Hint:* Introduce a `TAXBASE` rule = `GROSS − |SOCIALEMPLOYEE| − |HEALTH|`, then compute
  tax on `TAXBASE − NCZD`. Rewrite `INCOMETAX19`/`INCOMETAX25` to consume it.

- [ ] **Non-taxable part per taxpayer (NČZD) not applied.**
  *Why:* Every eligible employee with a signed *Vyhlásenie* gets €497.23/mo (2026) /
  €479.48/mo (2025) tax-free; omission over-taxes.
  *Hint:* New rule param `l10n_sk_nczd_monthly` (dated values). Add `hr.employee` boolean
  `l10n_sk_tax_declaration_signed`. Apply the high-income taper (start €26,083.13 annual base 2026).

- [ ] **Health employer rate is 10%, must be 11%.**
  *Why:* Wrong since 2024; under-charges employer cost on every slip.
  *Hint:* `HEALTHEMPLOYER` → 11; better, move to rule param `l10n_sk_health_rate_employer`.

- [ ] **Health employee rate must rise 4% → 5% for 2026.**
  *Why:* Confirmed 2026 change; 4% under-withholds from Jan 2026.
  *Hint:* Rule param `l10n_sk_health_rate_employee` with dated values 4% (…2025) / 5% (2026-01-01…).

- [ ] **Maximum monthly assessment base is 8477 (2017).**
  *Why:* Must be €15,730 (2025) / €16,764 (2026); all capped social funds mis-cap for
  high earners.
  *Hint:* Add dated values to `l10n_sk_monthly_taxable_max` (15730 from 2025-01-01, 16764
  from 2026-01-01). Keep the existing `min(GROSS, param)` pattern; keep accident un-capped.

- [ ] **Child tax bonus (daňový bonus na dieťa) entirely missing.**
  *Why:* €100 (<15y) / €50 (15–17y) per child, capped at 29/36/43/50/57/64% of tax base,
  with high-income taper — large net-pay effect.
  *Hint:* `hr.employee` fields for number of children by age tier; rule params for amounts,
  %-caps, taper threshold (€27,432 annual, 2026). New rule `CHILD_BONUS` credited against tax.

- [ ] **Income-tax threshold stale + missing 2026 progressive bands.**
  *Why:* 41445.46 is wrong (2025 band-1 = €47,537.98; 2026 band-1 = €43,983.32) and 2026
  adds 30% (>€60,349.21) and 35% (>€75,010.32) bands.
  *Hint:* Replace single threshold with dated band tables; compute monthly advance on the
  monthly base (band-1 monthly €3,665.28 for 2026), not on cumulative YTD gross.

---

## P2 — Completeness (legally required but narrower impact)

- [ ] **ZŤP / disabled employee handling.**
  *Why:* Health rate halves to 2.5%/5.5% (2026); disability social rules differ for
  pensioners.
  *Hint:* `hr.employee` `l10n_sk_ztp` boolean → select halved health rate param.

- [ ] **Health minimum base / doplatok (životné minimum).**
  *Why:* Combined health premium must reach the subsistence-minimum floor (€284.13, 2026);
  low-hours/part-month wages under-pay without a top-up.
  *Hint:* After computing health, top up to min(€45.45 combined, 2026) via a correction rule.

- [ ] **Agreements (dohody) DoVP / DoPČ structures.**
  *Why:* Common employment form with distinct contribution rules and hour limits (350/yr,
  10h/wk).
  *Hint:* New structure types + structures; OOP handling below.

- [ ] **Dohoda OOP for students/pensioners (€200) and seasonal DoPČ OOP (€762).**
  *Why:* Reduces pension-insurance base; without it dohodári are over-charged.
  *Hint:* Rule params + a pension-base reduction rule gated on an employee "OOP agreement"
  flag; exclude accident/guarantee from the reduction.

- [ ] **Meal allowance not computed per law.**
  *Why:* Employer must contribute ≥55% (range €3.84–€5.12, 2026); voucher vs financial
  contribution differ; must be exempt from tax and both contribution bases.
  *Hint:* Rule params for stravné/min voucher/max deductible; a version selector for
  voucher vs financial contribution; ensure the amount is excluded from GROSS and from the
  social/health assessment bases (not merely backed out in NET).

- [ ] **Statutory reporting / výkazy.**
  *Why:* Employers must file monthly: Mesačný výkaz poistného (Sociálna poisťovňa), Výkaz
  preddavkov (health insurers), and Prehľad/Hlásenie (Finančná správa).
  *Hint:* Add report generators (XML/CSV per official schemas) sourced from payslip lines.

- [ ] **Annual reconciliations.**
  *Why:* Ročné zúčtovanie zdravotného poistenia (RZZP) and annual tax reconciliation
  (ročné zúčtovanie preddavkov na daň) true up the year.
  *Hint:* Year-end wizard; typically separate from monthly run but expected of a complete
  localisation.

---

## P3 — Nice-to-have / robustness

- [ ] **Move all hardcoded rates to dated `hr.rule.parameter` values.**
  *Why:* 2025↔2026 differences (health, ceiling, bands, NČZD, bonus) should be data-driven,
  not code edits.
  *Hint:* One parameter per rate with `date_from` rows; rules read `_rule_parameter(...)`.

- [ ] **Minimum-wage data + validation (levels 1–6).**
  *Why:* Useful for compliance checks and minimum-wage-based surcharges.
  *Hint:* Rule params for the 6 monthly/hourly amounts; optional warning if contract wage
  below the level minimum.

- [ ] **Employee premium (zamestnanecká prémia).**
  *Why:* Rare but legally real low-income relief.
  *Hint:* Compute in annual reconciliation only.

- [ ] **NČZD on spouse (nezdaniteľná časť na manžela/manželku).**
  *Why:* Annual-only relief; completeness.

- [ ] **Wage-surcharges (príplatky) — night/weekend/holiday/overtime.**
  *Why:* Zákonník práce mandates minimum surcharges; not in the current module.
  *Hint:* Work-entry-type-driven allowance rules referencing minimum-wage-based rates.

- [ ] **Attachment/garnishment limits (zrážky zo mzdy).**
  *Why:* EE has raw `ATTACH_SALARY`/`CHILD_SUPPORT` inputs but no protected-minimum
  computation.
  *Hint:* Implement non-attachable amount based on subsistence minimum and dependents.
