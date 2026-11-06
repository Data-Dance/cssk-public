---
title: Historical social assessment register
summary: Reviewed historical fund bases and dated standard premiums for additional income; foundation for a paying slip and ZECN VPP integration.
verified: 19.0.1.2.0
---

## Purpose {#purpose}

Allocate income after insurance ends to the last insurance year's months under
[§139b](law:sk/2003/461#paragraf-139b). Keep employee/employer funds separate,
exact fractions for later settlements and cent-rounded monthly bases/premiums.
Exclude documented paid-at-ceiling months; do not redistribute near-ceiling
excess. Accident insurance remains uncapped.

## Operation {#operation}

Create a register from payroll declarations. Enter dates, assigned IČPV, gross
income and documentary references. **Prepare editable history** creates
month/fund rows. Review coverage, exact unreduced base, original assessed base,
nominal claimed OOP, effective ceiling, actual payment at ceiling and evidence
in every row. Preparation does not infer eligibility. Missing row evidence
blocks calculation. This is an editable fallback for history outside Odoo;
automatic import of confirmed payslips is a later step.

Calculate bases, review standard coverage without special relief, then
calculate premiums. OOP, maximum and every rate come from native dated
parameters for the historical month. No 2027-only lock remains. Missing
historical parameters raise; future legislative values still require review
and maintenance. Effective ceilings can be below the statutory maximum.

The optional hidden JSON ledger remains for API compatibility. It cannot be
combined with editable rows. Both representations explicitly cover all twelve
fund channels and every month, including uninsured channels.

## Evidence and integration {#integration}

Actions archive inputs/results and digests. Reset keeps archives; calculated
rows cannot be edited. Changed dated values invalidate retries.

Intended path: **historical evidence → bases → premiums → native paying slip,
health/tax/accounting → ZECN fund/month VPP**. The result rows will feed VPP and
the same register will supply the slip, avoiding duplicate historical input.
This module does not alter ordinary salary rules or bypass their period guard.

Not implemented here: automatic history import, eligibility adjudication,
special relief, negative corrections, health/tax, native posting, official VPP
or authority acceptance. This module alone does not complete #12. Synthetic
future parameter tests verify date-driven behavior, not future legal values.
