# l10n_sk_hr_payroll_oca: developer notes

Not user documentation: this file is not rendered into a page.

## Parameters

- Monthly salary structure *Slovakia: Regular Pay* (`SKMONTHLY`).
* **Social insurance** — sickness, old-age pension, disability, unemployment,
  guarantee, accident and reserve fund, split into employee and employer
  shares, capped at the maximum monthly assessment base (accident insurance is
  uncapped).
* **Health insurance** — employee and employer shares, the halved rate for
  persons with a disability (ZŤP), and a top-up (doplatok) to the minimum
  assessment base.
* **Income tax advance** — computed on the correct tax base
  (gross − employee social − employee health − the non-taxable part NČZD), with
  the progressive band table and the high-income taper of the NČZD.
* **Child tax bonus** (daňový bonus na dieťa) — per-child amounts by age tier,
  the percentage-of-tax-base cap by number of children, and the high-income
  taper; may result in a payout.
* **Meal allowance** (stravné) — meal-voucher and financial-contribution
  options with the statutory minimum employer contribution.
* All statutory rates and ceilings are stored as **dated rule parameters**
  (`hr.rule.parameter` / `hr.rule.parameter.value`), so the 2025 ↔ 2026
  differences are data, not code. `payslip.rule_parameter(code)` resolves the
  value effective at the payslip date.
