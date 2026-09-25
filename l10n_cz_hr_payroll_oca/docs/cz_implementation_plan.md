# Czech Payroll — Odoo Implementation Plan (EE + OCA)

Two modules, one legal model:
- **`l10n_cz_hr_payroll_ee`** — Enterprise, on `hr_payroll` (Odoo 19, uses `hr.version`). Structural twin of `l10n_sk_hr_payroll`.
- **`l10n_cz_hr_payroll_oca`** — CE/OCA, on the OCA `payroll` engine (18.0, uses `hr.contract`). Structural twin of `l10n_sk_hr_payroll_oca`.

Both must produce the **same numbers** from the same legal parameters (see `cz_payroll_legal.md`). Keep salary-rule **codes identical** across the two flavours so payslips, tests and reports line up.

The legal engine references `cz_payroll_legal.md` for every numeric value; this plan does not restate the law.

---

## 1. Module structure (mirror the SK twins)

### EE — `l10n_cz_hr_payroll_ee/`
```
__manifest__.py            depends: ['hr_payroll','hr_work_entry_holidays','hr_payroll_holidays'], countries:['cz'], auto_install:['hr_payroll'], license OEEL-1
__init__.py
models/
  __init__.py
  hr_version.py            l10n_cz_* contract fields + _get_whitelist_fields_from_template
  hr_employee.py           related fields onto version_id
  hr_payslip.py            _get_data_files_to_update (upgrade hook)
  hr_payroll_structure_type.py   _get_selection_schedule_pay -> [('monthly','Monthly')] for CZ
data/
  hr_rule_parameter_data.xml          hr.rule.parameter + hr.rule.parameter.value (dated)
  hr_salary_rule_category_data.xml    CZ categories, parented to hr_payroll.BASIC/GROSS/NET/ALW/DED
  hr_payroll_structure_type_data.xml  structure_type_employee_cz
  hr_payroll_structure_data.xml       CZMONTHLY structure (+ report_id, type_id)
  hr_salary_rule_data.xml             the rules (each carries struct_id)
  l10n_cz_hr_payroll_demo.xml
views/  hr_contract_template_views.xml, hr_employee_views.xml, report_payslip_templates.xml, hr_payroll_report.xml
```

### OCA — `l10n_cz_hr_payroll_oca/`
```
__manifest__.py            depends: ['payroll'], countries:['cz'], license AGPL-3
models/
  __init__.py              order: hr_rule_parameter first
  hr_rule_parameter.py     reimplement hr.rule.parameter + hr.rule.parameter.value + _get_parameter_value
  hr_contract.py           l10n_cz_* fields (NOT hr.version)
  hr_employee.py           related via contract_id
  hr_payslip.py            rule_parameter(code) accessor + _get_baselocaldict injects relativedelta
data/
  hr_salary_rule_category_data.xml    self-define BASIC/ALW/DED/GROSS/NET/COMP + CZ categories
  hr_rule_parameter_data.xml          same values/dates as EE
  hr_salary_rule_data.xml             rules WITHOUT struct_id (attribute-access python)
  hr_payroll_structure_data.xml       structure with rule_ids m2m — LOADED AFTER rules
security/ir.model.access.csv          access to hr.rule.parameter[.value] via payroll.group_payroll_*
views/  hr_contract_views.xml
```

---

## 2. Salary-rule categories

EE inherits Odoo's built-ins `BASIC/GROSS/NET/ALW/DED/COMP`; OCA must **self-define** them (the OCA engine ships none). Both then add the CZ-specific ones below (same codes both flavours):

| Code | Name | Parent |
|---|---|---|
| SOCIALEE | Social Insurance (Employee) | DED |
| SOCIALER | Social Insurance (Employer) | COMP |
| HEALTHEE | Health Insurance (Employee) | DED |
| HEALTHER | Health Insurance (Employer) | COMP |
| TAXBASE | Tax Base | — (memo) |
| INCOMETAX | Income Tax Advance | DED |
| TAXCREDIT | Tax Credits | — (memo) |
| CHILDBEN | Child Benefit / Bonus | — (memo) |
| MEALEE | Meal Allowance (Employee) | ALW |
| SOCIALEETOT / SOCIALERTOT / HEALTHEETOT / HEALTHERTOT / INCOMETAXTOT | reporting totals | — |

---

## 3. Rule parameters (`hr.rule.parameter`, dated values)

Codes shared by both flavours; EE reads them via `payslip._rule_parameter(code)`, OCA via `payslip.rule_parameter(code)`. Values from `cz_payroll_legal.md` master table, with `date_from` 2025-01-01 and 2026-01-01 rows.

| Code | Meaning | 2025 | 2026 |
|---|---|---|---|
| `l10n_cz_avg_wage` | průměrná mzda / month | 46557 | 48967 |
| `l10n_cz_social_max_base` | max annual social base | 2234736 | 2350416 |
| `l10n_cz_social_rate_ee` | employee social % | 7.1 | 7.1 |
| `l10n_cz_social_rate_er` | employer social % | 24.8 | 24.8 |
| `l10n_cz_health_rate_ee` | employee health % | 4.5 | 4.5 |
| `l10n_cz_health_rate_er` | employer health % | 9.0 | 9.0 |
| `l10n_cz_health_min_base` | min health base (=min wage) | 20800 | 22400 |
| `l10n_cz_tax_rate_1` / `_2` | 15 / 23 | 15/23 | 15/23 |
| `l10n_cz_tax_threshold_month` | 3× avg wage | 139671 | 146901 |
| `l10n_cz_credit_taxpayer` | sleva na poplatníka / mo | 2570 | 2570 |
| `l10n_cz_credit_ztpp` | ZTP/P holder / mo | 1345 | 1345 |
| `l10n_cz_credit_disab_12` / `_3` | invalidita I-II / III /mo | 210/420 | 210/420 |
| `l10n_cz_child_1` / `_2` / `_3` | child benefit tiers / mo | 1267/1860/2320 | 1267/1860/2320 |
| `l10n_cz_bonus_min_income_month` | ½ min wage | 10400 | 11200 |
| `l10n_cz_dpp_threshold` | DPP insurance threshold | 11500 | 12000 |
| `l10n_cz_dpc_threshold` | DPČ/small threshold | 4000 | 4500 |
| `l10n_cz_meal_exempt` | stravenkový paušál/shift | 123.90 | 129.50 |
| `l10n_cz_min_wage` | minimum wage / mo | 20800 | 22400 |

`parameter_value` may be a tuple/dict where handy (e.g. `(1267,1860,2320)` for child tiers) — OCA `safe_eval`s the literal, EE does too.

---

## 4. Custom contract / employee fields

Defined on **`hr.version`** (EE) / **`hr.contract`** (OCA); surfaced on `hr.employee` as related. Prefix `l10n_cz_`. All guarded by the payroll user group (EE `hr_payroll.group_hr_payroll_user`; OCA `payroll.group_payroll_user`).

| Field | Type | Purpose |
|---|---|---|
| `l10n_cz_tax_declaration` | Boolean | prohlášení poplatníka signed → enables monthly credits & child benefit |
| `l10n_cz_children_t1` / `_t2` / `_t3` | Integer | number of children at tier 1 / 2 / 3+ (drives daňové zvýhodnění) |
| `l10n_cz_children_ztpp` | Integer | of which hold ZTP/P (benefit doubled) |
| `l10n_cz_claim_ztpp` | Boolean | employee holds ZTP/P → sleva ZTP/P |
| `l10n_cz_disability` | Selection none/1_2/3 | invalidity degree → sleva na invaliditu |
| `l10n_cz_is_state_insured` | Boolean | státní pojištěnec → skip HI top-up-to-minimum |
| `l10n_cz_agreement_type` | Selection standard/dpp/dpc | employment vs DPP vs DPČ (thresholds & srážková daň) |
| `l10n_cz_dpp_notified` | Boolean | "oznámená dohoda" → higher DPP threshold applies |
| `l10n_cz_meal_allowance` | Monetary | per-shift meal allowance (like SK meal voucher fields) |
| `l10n_cz_ytd_social_base` | (computed) | optional cache for annual cap; otherwise summed from prior payslips |

EE: add each to `_get_whitelist_fields_from_template()`. OCA: expose on the `hr.contract` form via an inherited view inside `group[@name='salary']`.

---

## 5. Salary-rule list (codes identical in both flavours)

Sequences follow the SK template (BASIC 1, meal 80, GROSS 100, insurances 110–160, tax 170, deductions 174–199, NET 200, totals 500+). Formulas are pseudo-python. **Two dialects:**
- **EE:** `categories['X']`, `worked_days['X']`, `inputs['X']`, `result_rules['X']['total']`, `payslip._rule_parameter('c')`, `payslip.paid_amount`, states `['paid','validated']`.
- **OCA:** `categories.X`, `worked_days.X`, `inputs.X`, `result_rules.X.total`, `'X' in obj.dict`, `payslip.rule_parameter('c')`, `contract.wage`, state `'done'`. Inject `relativedelta` in `_get_baselocaldict`.

| Seq | Code | Name | Category | Formula (EE dialect; result_rate in %) |
|---|---|---|---|---|
| 1 | `BASIC` | Basic Salary | BASIC | `result = payslip.paid_amount` (OCA: `contract.wage`) |
| 80 | `MEAL` | Meal Allowance | MEALEE | `result_qty = worked_days['WORK100'].number_of_days; result = min(version.l10n_cz_meal_allowance, payslip._rule_parameter('l10n_cz_meal_exempt'))` |
| 100 | `GROSS` | Gross (Superhrubá abolished) | GROSS | `result = categories['BASIC'] + categories['ALW']` |
| 110 | `SOCIALEE` | Social Insurance (EE) 7.1% | SOCIALEE | `base = min(categories['GROSS'], _annual_cap_remaining()); result = base; result_rate = -payslip._rule_parameter('l10n_cz_social_rate_ee')` |
| 111 | `SOCIALER` | Social Insurance (ER) 24.8% | SOCIALER | same base; `result_rate = payslip._rule_parameter('l10n_cz_social_rate_er')`; `appears_on_payslip=False` |
| 120 | `HEALTHEE` | Health Insurance (EE) 4.5% | HEALTHEE | `base = categories['GROSS'] if version.l10n_cz_is_state_insured else max(categories['GROSS'], payslip._rule_parameter('l10n_cz_health_min_base')); result = base; result_rate = -payslip._rule_parameter('l10n_cz_health_rate_ee')` |
| 121 | `HEALTHER` | Health Insurance (ER) 9% | HEALTHER | `result = categories['GROSS']; result_rate = 9`; `appears_on_payslip=False` |
| 130 | `TAXBASE` | Tax Base | TAXBASE | `result = categories['GROSS']` (base = gross; round up to 100 in tax rules) |
| 170 | `INCOMETAX` | Income Tax Advance (15/23) | INCOMETAX | two-band on `TAXBASE` rounded up to 100; `thr = payslip._rule_parameter('l10n_cz_tax_threshold_month'); tax = 0.15*min(base,thr) + 0.23*max(base-thr,0); result = tax; result_rate = -1` |
| 171 | `TAXCREDIT` | Tax Credits (slevy) | TAXCREDIT | if `version.l10n_cz_tax_declaration`: sum poplatník + ZTP/P + invalidita; `result = min(credits, -INCOMETAX)` (credit cannot exceed tax); positive line reducing DED |
| 172 | `CHILDBEN` | Child Benefit / Bonus | CHILDBEN | `benefit = t1*p1 + t2*p2 + t3*p3 (+ ztpp doubling)`; `tax_after = max(-INCOMETAX - TAXCREDIT,0)`; `result = min(benefit, tax_after)` as credit; **bonus** = `benefit - that` paid only if monthly income ≥ `l10n_cz_bonus_min_income_month` → separate positive `CHILDBONUS` line |
| 173 | `CHILDBONUS` | Daňový bonus (payout) | ALW | see above; condition `version.l10n_cz_tax_declaration and gross >= threshold` |
| 174 | `ATTACH_SALARY` / `ASSIG_SALARY` / `CHILD_SUPPORT` | garnishments | DED | input-driven (copy SK verbatim); real nezabavitelná-částka logic is P3 |
| 180 | `SICKPAY` | Náhrada mzdy (days 1–14) | ALW | P2: `result = 0.60 * reduced_avg_hourly * sick_hours` using `WORK_SICK` worked-days code |
| 198 | `DEDUCTION` | Deduction (input) | DED | copy SK |
| 199 | `REIMBURSEMENT` | Reimbursement (input) | ALW | copy SK |
| 200 | `NET` | Net Salary | NET | `result = BASIC + categories['ALW'] + categories['DED'] - result_rules['MEAL']['total']` (meal is a benefit, not cash-in-hand unless paid; mirror SK's meal-exclusion pattern) |
| 500 | `SOCIALEETOT` / `SOCIALERTOT` | Social totals | *TOT | `result = categories['SOCIALEE']` / `['SOCIALER']` |
| 501 | `HEALTHEETOT` / `HEALTHERTOT` | Health totals | *TOT | reporting only |
| 510 | `INCOMETAXTOT` | Income Tax total | INCOMETAXTOT | `result = -categories['INCOMETAX']` |
| 520 | `EMPLOYERCOST` | Total employer cost | COMP | `result = GROSS + categories['SOCIALER'] + categories['HEALTHER']` |

Helper `_annual_cap_remaining()` (implement as a payslip method both flavours): sum prior-year `GROSS` (EE `_get_line_values`; OCA `sum(get_salary_line_total('GROSS'))` over `state='done'` YTD payslips), then `min(month_gross, max(cap - ytd, 0))`. Mirror the SK income-tax YTD pattern exactly for the date filters.

**DPP/DPČ handling** (rules gated on `l10n_cz_agreement_type`): if `dpp` and gross < `l10n_cz_dpp_threshold` (or `dpc` and gross < `l10n_cz_dpc_threshold`) → social & health rules return 0; if DPP without prohlášení and under threshold → replace advance with 15 % `SRAZKOVA_DAN` rule (final withholding). This is P2 scope.

---

## 6. EE vs OCA — differences the implementation must handle

| Concern | EE (`l10n_cz_hr_payroll_ee`) | OCA (`l10n_cz_hr_payroll_oca`) |
|---|---|---|
| Contract model | `hr.version` (fields + `_get_whitelist_fields_from_template`) | `hr.contract` (plain fields) |
| Employee related | `related=version_id.*` | `related=contract_id.*` |
| Wage variable | `payslip.paid_amount` (proration-aware) | `contract.wage` (full monthly) |
| Rule parameters | built-in `hr.rule.parameter` + `payslip._rule_parameter('c')` | **reimplement** `hr.rule.parameter`/`.value` model + `payslip.rule_parameter('c')` (`_get_parameter_value` picks latest `date_from ≤ date_to`, `safe_eval`) |
| Default categories | provided (`hr_payroll.BASIC/GROSS/NET/ALW/DED/COMP`) | **none — self-define** all six then reference locally |
| Structure ↔ rules | each rule has `struct_id` | structure holds `rule_ids` m2m; **structure file loaded AFTER rules** |
| `hr.payroll.structure.type` | exists (`type_id`, `default_struct_id`, `_get_selection_schedule_pay`) | **does not exist** — omit entirely |
| Structure `report_id` | set to payslip report | field absent — omit |
| Browsable access | subscript: `categories['X']`, `inputs['X']`, `result_rules['X']['total']`, `'X' in worked_days` | attribute: `categories.X`, `inputs.X`, `result_rules.X.total`, `'X' in obj.dict` |
| localdict extras | `relativedelta` already present | inject via `_get_baselocaldict` override |
| Payslip state (YTD filter) | `['paid','validated']` | `'done'` |
| YTD line sums | `payslip._get_line_values(['GROSS'], compute_sum=True)` | `sum(p.get_salary_line_total('GROSS') for p in ...)` |
| Security group xmlids | `hr_payroll.group_hr_payroll_user` | `payroll.group_payroll_user` / `payroll.group_payroll_manager` (+ ir.model.access rows for the reimplemented parameter models) |
| Worked-days codes | `WORK100` etc. from `hr_work_entry_holidays` | base `payroll` WD codes (`WORK100`); sick code needs defining |
| License / manifest | OEEL-1, `auto_install`, `countries:['cz']` | AGPL-3, `depends:['payroll']` |
| Upgrade hook | `_get_data_files_to_update` re-imports data on upgrade | not present (standard OCA load) |

**Rule of thumb:** author the EE `hr_salary_rule_data.xml` first, then mechanically transform to OCA per the dialect table (this is exactly how the SK-OCA twin's header comment documents the port).

---

## 7. Phased roadmap

### P1 — Core monthly payslip correctness (standard employment)
- [ ] EE + OCA module skeletons, manifests, `__init__`, security.
- [ ] Categories (EE inherit / OCA self-define), structure(s), structure type (EE only).
- [ ] `hr.rule.parameter` values for 2025 + 2026 (both flavours; OCA reimplement model).
- [ ] Contract/employee fields (§4) + views + whitelist (EE).
- [ ] Rules: BASIC, GROSS, SOCIALEE/ER (with 48× annual cap), HEALTHEE/ER (with min-base top-up & state-insured skip), TAXBASE, INCOMETAX (15/23 monthly), TAXCREDIT (poplatník/ZTP/P/invalidita), CHILDBEN + CHILDBONUS, NET, employer-cost + reporting totals.
- [ ] Tests: 3–4 golden payslips (avg wage, above-cap, min-wage part-timer, high earner into 23 %) cross-checked vypocet.cz/kalkulačka; parity EE == OCA.
- [ ] Meal allowance rule (stravenkový paušál exempt limit).

### P2 — Dohody, bonus edge-cases, sickness
- [ ] DPP/DPČ thresholds + "oznámená dohoda" gating; DPP 15 % srážková daň rule.
- [ ] Daňový bonus income tests (monthly ½ min wage; annual 6× via roční zúčtování note).
- [ ] Náhrada mzdy days 1–14 (60 % reduced avg hourly, redukční hranice, `WORK_SICK` worked-day code, employer-only, no insurance).
- [ ] Working-pensioner social sleva (6.5 %).

### P3 — Reporting / výkazy & annual
- [ ] Real srážky ze mzdy (nezabavitelná částka 14 101,50 / 1.9× 31 521 method, thirds).
- [ ] Monthly statements: **Přehled o výši pojistného** (ČSSZ), **Přehled** for health insurers, **JMHZ** DPP monthly report (from 04/2026).
- [ ] **ELDP** (evidenční list důchodového pojištění) export.
- [ ] **Roční zúčtování daně** (annual tax reconciliation: spouse credit, annual bonus, non-taxable items).
- [ ] Payslip PDF report (EE `report_id`; OCA `report/report.xml`).

---

## 8. Risks & open questions

- **Rounding rules** — monthly tax base rounded **up to whole 100 Kč** (§38h ZDP); social/health premium rounding (to whole koruna, direction) must be confirmed against ČSSZ methodology before go-live; small rounding diffs will fail golden-payslip parity tests.
- **48× annual cap mechanics** — cap is annual/cumulative, applied to the employee contribution; needs a reliable YTD base (payslip search vs a stored `l10n_cz_ytd_social_base`). Mid-year hires and multiple concurrent employers complicate it.
- **Health min-base top-up** — the 13.5 % shortfall on (min wage − actual) is borne **by the employee**; confirm which portion and interaction with unpaid absences / part-month.
- **DPP notification regime** — "oznámená dohoda" logic and the JMHZ monthly reporting (live 04/2026) are moving targets; treat as P2/P3 and re-verify against ČSSZ.
- **State-insured detection** — `l10n_cz_is_state_insured` is a manual flag; no automatic derivation from age/student/pension status in v1.
- **OCA `paid_amount` gap** — OCA has no proration-aware `paid_amount`; part-month proration must be handled via worked-days or a custom computation, else OCA and EE diverge for partial months.
- **2025 vs 2026 parameter switch** — all dated via `hr.rule.parameter` `date_from`; ensure payslip uses `date_to` for lookups (matches SK-OCA `_get_parameter_value`).
- **Superhrubá confirmation** — base = gross since 2021 (no 1.34× gross-up); documented, but keep a guard test so a future regression is caught.
- **Zaručený plat** — public-sector only; not modelled (private-sector minimum wage only). Confirm the target user base is private sector.
