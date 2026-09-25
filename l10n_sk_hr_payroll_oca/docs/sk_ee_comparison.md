# SK Payroll — Odoo EE module vs. legal reference

Module analysed: `/home/rex/Odoo/19.0-EE/l10n_sk_hr_payroll/` (Odoo 19.0 EE, author Odoo S.A.,
version 1.0). Cross-referenced against `sk_payroll_legal.md`.

## How the EE module is built

- **Almost every rate is hardcoded** in `data/hr_salary_rule_data.xml` via `result_rate = …`
  in the Python compute of each salary rule. There are **only two rule parameters**
  (`data/hr_rule_parameter_data.xml`):
  - `l10n_sk_monthly_taxable_max` = **8477**, `date_from` 2017-01-01
  - `l10n_sk_income_tax_threshold` = **41445.46**, `date_from` 2017-01-01
  Both are stale (dated 2017) and neither matches current law.
- Single structure `SKMONTHLY` ("Slovakia: Regular Pay"), monthly only
  (`hr_payroll_structure_type._get_selection_schedule_pay` forces monthly).
- Models add only two fields: `l10n_sk_meal_voucher_employee` /
  `l10n_sk_meal_voucher_employer` on `hr.version` (flat amounts, no legal logic).
- No `hr.employee` fields for children, disability (ZŤP), signed declaration, tax-bonus
  eligibility, number of dependents, etc.

## Requirement-by-requirement

Legend: ✅ implemented & current · 🟨 partial / outdated · ❌ missing

### Social insurance
| Requirement | Status | Notes |
|---|---|---|
| Sickness ee/er 1.4/1.4% | ✅ | `SICK` −1.4 / `SICKEMPLOYER` 1.4 |
| Old-age pension ee/er 4/14% | ✅ | `PENSION` −4 / `PENSIONEMPLOYER` 14 |
| Disability ee/er 3/3% | ✅ | `DISABILITY` −3 / `DISABILITYEMPLOYER` 3 |
| Unemployment ee 1% / er 0.5% | ✅ | `UNEMPLOYMENT` −1 / `UNEMPLOYMENTEMPLOYER` 0.5 |
| Short-time-work er 0.5% | ✅ | `SHORTTIMEEMPLOYER` 0.5 |
| Guarantee er 0.25% | ✅ | `GUARANTEEEMPLOYER` 0.25 |
| Accident er 0.8%, **no ceiling** | ✅ | `ACCIDENT` 0.80 on `categories['GROSS']` (correctly un-capped) |
| Reserve fund er 4.75% | ✅ | `RESERVEFUNDEMPLOYER` 4.75 |
| Max monthly assessment base | 🟨 | Capped via `min(GROSS, l10n_sk_monthly_taxable_max)` — good pattern, **but value 8477 is wrong**; should be €15,730 (2025) / €16,764 (2026) |
| Ceiling **not** applied to accident | ✅ | Accident uses raw GROSS — correct |

**Verdict:** social rates are all correct; the only social defect is the outdated ceiling
value. Rates are hardcoded, not parameterised (maintenance risk but currently correct).

### Health insurance
| Requirement | Status | Notes |
|---|---|---|
| Employer 11% | ❌ | `HEALTHEMPLOYER` hardcoded **10** — wrong since 2024 (should be 11%). **Under-charges employer.** |
| Employee 4% (2025) | ✅ (2025 only) | `HEALTH` −4 correct for 2025 |
| Employee 5% (2026) | ❌ | Must become 5% from 2026; still 4% |
| No max base on health | ✅ | Uses `categories['GROSS']` (un-capped) — correct |
| Min base / doplatok (životné minimum) | ❌ | Not implemented |
| ZŤP halved rates | ❌ | No disability flag, no halved rate |
| Health OOP (€380) | ❌ | Not implemented |
| Ročné zúčtovanie (RZZP) | ❌ | Not implemented (arguably out of monthly scope) |

### Income tax
| Requirement | Status | Notes |
|---|---|---|
| Tax base = gross − ee social − ee health − NČZD | ❌ | **Tax is computed on raw `categories['GROSS']`** in `INCOMETAX19`/`INCOMETAX25`. Contributions are **not** deducted from the base, and NČZD is **not** applied at all. Materially over-states tax. |
| Non-taxable part (NČZD) | ❌ | Completely absent |
| 19% / 25% bands | 🟨 | Present but threshold `l10n_sk_income_tax_threshold` = 41445.46 is stale (2025 = €47,537.98; 2026 band-1 = €43,983.32) and the module compares **cumulative yearly GROSS** to the annual threshold rather than a proper monthly base |
| 2026 30% / 35% bands | ❌ | Not implemented (progressive reform) |
| Child tax bonus (age tiers, % caps, taper) | ❌ | Entirely absent — big net-pay impact |
| Employee premium (zamestnanecká prémia) | ❌ | Absent (minor) |

The tax logic in `INCOMETAX19`/`INCOMETAX25` is a rough YTD-threshold split on gross. It
does not reflect the Slovak monthly-advance method and omits both the contribution
deduction and NČZD. This is the module's most serious correctness gap.

### Minimum wage
| Requirement | Status | Notes |
|---|---|---|
| Monthly / hourly minimum wage | ❌ | No parameter, no validation |
| Work-difficulty coefficients (1–6) | ❌ | Not modelled |

### Meal allowance
| Requirement | Status | Notes |
|---|---|---|
| Employer 55% obligation | 🟨 | Only two free-form amount fields on the version; no % logic, no link to stravné, no min/max enforcement |
| Financial-contribution vs voucher | ❌ | Not distinguished |
| Exemption from tax & contribution base | 🟨 | `MEALEMPLOYEE`/`MEALEMPLOYER` are quantity-flagged on `WORK100` and backed out again in `NET`; they are not properly excluded from GROSS/assessment bases in a principled way |

### Agreements (dohody)
| Requirement | Status | Notes |
|---|---|---|
| DoVP / DoPČ structures | ❌ | Only one employment structure exists |
| Student/pensioner OOP €200 | ❌ | Absent |
| Seasonal DoPČ OOP €762 | ❌ | Absent |

### Reporting / výkazy
| Requirement | Status | Notes |
|---|---|---|
| Mesačný výkaz poistného (Sociálna poisťovňa) | ❌ | None |
| Výkaz preddavkov (zdravotná poisťovňa) | ❌ | None |
| Prehľad / Hlásenie (Finančná správa) | ❌ | None |

## Are the values current?
- **Social rates:** current ✅ (correct for 2025 & 2026).
- **Social ceiling:** 🟨 stale (8477 vs 15,730/16,764).
- **Health employer:** ❌ stale (10% vs 11%).
- **Health employee:** ✅ for 2025, ❌ for 2026 (needs 5%).
- **Income tax:** ❌ structurally incomplete and stale threshold.
- **Everything requiring employee attributes** (children, ZŤP, declaration): ❌ absent.

## Hardcoded vs parameterised summary
All contribution rates and both tax rates are **hardcoded** in the salary-rule Python.
Only the ceiling and the tax threshold are rule parameters — and both are outdated. A
correct rewrite should move every rate into dated `hr.rule.parameter` values so 2025 vs
2026 differences (health 4→5%, ceiling, tax bands, NČZD, bonus) are data-driven.
