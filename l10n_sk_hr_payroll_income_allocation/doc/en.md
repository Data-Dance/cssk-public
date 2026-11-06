# Historical social assessment register — explicit limited scope

This is a self-contained OCA-payroll add-on with no dependency on private/local
adapters. It adds `l10n.sk.income.allocation` and calculated fund/month rows to
the payroll declarations menu. It does not change existing payslip rules or
declare the complete post-termination payroll workflow implemented.

## Calculation and statutory references

Reviewed vintage: settlement in2027, last insurance year2026/2027, EUR.
The base calculation uses the last insurance year and explicit historical
insurance/ceiling facts under [461/2003§139b](https://static.slov-lex.sk/static/SK/ZZ/2003/461/20270101.print.html).
Claimed nominal agreement OOP is200for2026 or300for2027; the original utilized
deduction is not a new claim. Full paid-ceiling months are excluded per channel;
near-ceiling excess is not reassigned to other months. The accident channel is
uncapped. Bases are floored to cents; exact fractions retain the unreduced
history for subsequent settlements. No residual cent is assigned to the final
month. Coverage and effective partial-month/concurrent-employment ceilings are
reviewed inputs, not inferred personal eligibility.

The separate standard-premium action requires an explicit review reference for
coverage, standard rates and absence of special relief. It applies §§129–137:
NP1.4/1.4, SP4/14, IP3/3, PVN1 employee and0.5/1 employer depending on PFP
coverage, UP0.8 employer, GP0.25 employer, RFS4.75 employer, PFP0.5 employer.
Only insured channels are charged. Each additional fund/month premium is
floored before totals. This is the premium on each newly assessed base, not a
recalculation by subtracting two rounded cumulative premium totals.

The source for allocation and ceiling-month exclusion is also summarized by
[Sociálna poisťovňa](https://www.socpoist.sk/kto-som/zamestnavatel/zasielanie-vykazov-dokladov/spravne-vyplnit-vykazy-poistneho).
Legal interpretation and unsupported workflows remain subject to review.

## Input ledger

The `ledger` JSON list covers every month of insurance in the last insurance
year, including uninsured months. Each item has `month` (`YYYY-MM`) and a
`funds` object containing all twelve channels:

`np_ee,np_er,sp_ee,sp_er,ip_ee,ip_er,pvn_ee,pvn_er,up_er,gp_er,rfs_er,pfp_er`.

Every channel supplies exactly:

```json
{"insured": true, "raw_before": "200", "base_before": "0",
 "oop": "300", "cap": "17820", "paid_at_cap": false}
```

`raw_before` also accepts exact fraction strings returned as `raw_after` by an
earlier calculation. Uninsured channels have zero bases/OOP. `cap:null` is used
for accident insurance and inactive channels; insured capped channels require
the reviewed effective ceiling. `paid_at_cap` is a documented payment fact,
not inferred merely because the computed base equals the maximum.

Original bases must reconcile with unreduced income, nominal OOP and ceiling.
Every employee and employer channel is separate, so their remaining ceilings
need not be equal. The supplied facts, not the arithmetic engine, decide who
was insured and entitled to a deduction in each period.

## Evidence, retry and limitations

Source changes require explicit reset. Each calculation creates a private
JSON attachment with inputs, results and a digest. Reset preserves archives.
Retries preserve existing rows and attachments. The premium review is frozen
after premium calculation and cleared on reset. Normal payroll-user access
and allowed-company scope are tested.

A synthetic three-month200/month agreement with nominal OOP300 and a late400
has additional pension bases33.33each, total99.99; accident bases133.33each,
total399.99. Standard employee social3.99, employer22.89, total26.88. Gross
remains400. These values are not a net-pay calculation.

Still outside scope: automatic source-history/insured-interval import, personal
eligibility, special contribution relief, negative corrections, health
insurance, income tax, native payslip creation/posting, VPP export and portal
acceptance. Future work must use the same historical evidence for payroll and
reporting; this register must not be advertised as completing issue12's ZECN
workflow. Tests cover arithmetic and the register, not an accepted live filing.
