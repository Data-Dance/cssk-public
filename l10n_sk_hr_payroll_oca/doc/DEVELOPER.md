# l10n_sk_hr_payroll_oca: developer notes

Not user documentation: this file is not rendered into a page.

## Parameters

The BASIC rule delegates to `l10n_sk_basic_salary(contract, worked_days,
scheduled_hours=None)`. Override it cooperatively rather than replacing the
salary-rule body. An integration calculating dated wage segments can pass
each segment's whole-period calendar divisor. Aggregate the wage into one
monthly BASIC before evaluating monthly insurance and tax rules; this hook
does not itself select or consolidate historical employment versions.

For a payslip-specific monthly wage input, override
`_l10n_sk_monthly_cash_wage(contract)`. Its default is the real contract wage.
The BASIC helper resolves this scalar once and applies its existing absence
and calendar proration; hourly pay does not use it. Keep source qualification,
input review and immutable evidence in the supplying integration. The hook
does not authorize changing a posted payslip or bypassing statutory checks.
The probable-hourly-earnings fallback uses this same input when the determining
quarter has insufficient worked time. A qualifying actual-quarter average
continues to use the retained historical earnings.

The hook must be a pure function of the payslip and the contract it receives,
without side effects. Dated-segment integrations can call `super()` once per
segment, so the hook may be resolved more than once for a single payslip.

This seam belongs to the OCA engine. Enterprise BASIC reads `payslip.paid_amount`
from worked-day amounts, which read the version wage directly; there is no
equivalent single hook in `l10n_sk_hr_payroll_ee` at present.

The OCA WORK100 source includes scheduled absence time. The helper subtracts
the common `l10n_sk_absence_codes()` once for both monthly and hourly wages.
Leave compensation remains in its own salary rule and category.

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

## OCA recording integration

Only compute_sheet receives the in-process recording capability. Direct
get_lines_dict/_get_payslip_lines and JSON-shaped context flags cannot modify
evidence. Each charging rule emits the base/rate/amount it actually used.
Custom rule quantities or invalid optional facts leave evidence missing without
preventing the native calculation. The shared statutory profile is stored once;
restricted birth numbers are not copied into it.

A payslip records only when `_get_employee_contracts()` (the contracts
`get_lines_dict()` computes over) is exactly one contract of its employee and
company. The identity keeps `contract_id`, which an API-created payslip
leaves empty; the reader also requires the profile's version to be the
contract of the payslip lines (which must be `contract_id` when set), so identity and
profile describe the same computation. An emitted base is the expression its
rule charged on (the rule's own variable where the frozen formula has one), and
an exemption that zeroes a premium zeroes its base; a test compares the two in
the rule ASTs.

The native refund adapter reads the original evidence and supplies its direction
and effective pairing. Historical records are not backfilled. Frozen original
formula JSON plus AST/runtime comparisons protect this evidence contribution's
arithmetic boundary. Reference-arithmetic fixtures remove the optional
MIN_WAGE_TOPUP rule from their test structure so their named low/subcent inputs
remain those inputs; the surcharge module tests the statutory top-up itself.

## Developer extension: annual January tax facts

`l10n.sk.tax.reconciliation._l10n_sk_annual_january_tax_version()` is a
singleton reader shared by the annual pension default and `action_compute`.
Its default delegates to the dated employee reader with the reconciliation's
company and tax year; the existing draft pension fallback remains unchanged.
An extension may supply a separately reviewed native version for annual
income after employment ended. It must validate the employee, company, tax
year and underlying January declaration. Keep the reader free of writes and
safe for repeated calls. This hook neither reviews a fact nor reopens an
employment, changes monthly payroll or selects annual income. The annual
company and pension-consistency checks still run. This is the OCA engine's
annual model; other engines need their own corresponding adapter.
