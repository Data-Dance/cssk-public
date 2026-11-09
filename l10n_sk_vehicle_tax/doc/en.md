---
title: Motor vehicle tax — DMVv25
summary: Prepare Slovak calendar-year motor vehicle tax from the native fleet register.
verified: 19.0.1.1.0
---

Accounting → Reporting → Statutory Reports → Motor vehicle tax.

## Scope {#scope}

Slovak legal entities with an ordinary calendar-year period, EUR amounts and
L1e–L7e, M1 or N1 vehicles. Liability uses reviewed whole months, independently
of VAT deduction, fuel expense percentages and mileage records. Other vehicle
categories, exemptions, combined transport, special short periods and repeated
liability intervals for the same registration are outside this edition.
The application blocks these unsupported selections or duplicate rows rather
than classifying them as an ordinary vehicle.

## Preparing a return {#preparation}

Use **Fleet → Vehicles → Slovak vehicle tax** to record the certificate facts.
The first registration is separate from the company's acquisition/registration
date. Power for electric vehicles must be in kW. Document hybrid status before
claiming its reduction. This edition calculates ordinary taxpayers a/b;
record exemptions/outside-scope grounds explicitly instead of discarding a car.

**Add company fleet vehicles** includes vehicles sold or archived during the
year. Review the imported snapshots. A later fleet edit requires **Refresh
fleet snapshot** and a new review on the draft return. Technical facts are not
retyped into a parallel register. Liability comes from acquisition/registration
and cancellation events; the engine converts their actual dates to statutory
month boundaries. A section 8 exception has an explicit dated override and
reason on the fleet record. No trip-log module is required.

1. Complete the company's DIČ and registered address. VAT registration is not
   required. Street/house number use the common localization address helper.
2. Review the ordinary-period scope, complete taxable fleet, technical documents,
   Slovak registration, taxpayer status, first registration and actual liability
   dates. Invoice dates are not automatically liability dates. Include electric
   vehicles even when their tax is zero.
3. Enter actual paid advances, with evidence also for a reviewed zero. A tax
   payment is not automatically an advance. Review annual adjusted rates for
   the entire fleet taxable at the following 1 January. The proposal button
   uses known vehicles and clears the review evidence; additions/disposals and
   the applicable next-year rate edition still require review.
4. Calculate. Inspect per-vehicle segments and totals. Export uses the common
   statutory pipeline, QWeb and the unchanged official DMVv25 XSD. Each rate
   segment is rounded down separately; the monthly fraction is not rounded.
   The statutory small-payment threshold does not erase the return's tax row.
5. Download the XML. An unfiled calculation/export becomes stale if its facts,
   company identification, template or edition change. Reset and recalculate.

## Corrections and retained filings {#corrections}

Recording a filing requires a reference and actual confirmation evidence.
Only one regular filing is allowed per company/year, including concurrent
workers. Use a correction linked to that original for subsequent filings.
This action records a fact; it does not transmit the return. The exact XML,
calculation and source workpaper are retained. A filed return cannot be edited,
reset or deleted. Its download does not reinterpret today's company data.

Prepare a separate **corrective** return before the ordinary deadline; it is a
complete replacement. After that deadline use **additional**, with discovery
date and reviewed grounds/filing eligibility, including any audit restrictions.
The latest retained filing of the same company/year must be the baseline.
Reconcile every previous vehicle once, including unchanged vehicles, and add
newly discovered vehicles as needed. Prior-vehicle links make differences
explicit even when a registration number or technical datum was corrected.

To completely remove an erroneous former liability, retain its linked row,
correct the actual liability dates to outside the return year, explicitly
review complete removal and document the grounds. The result preserves the
original tax, zero corrected tax and signed difference. Deleting the former
vehicle without reconciliation is refused.

Additional returns carry the signed vehicle and aggregate differences and keep
the original advances. Later tax payments must not be relabelled as advances.
A changed projected-tax row does not automatically change the already
applicable advance schedule. A separate company-IBAN repayment request requires
a positive overpayment and review; it is not a received refund. Such a request
is cleared when preparing a correction, preventing accidental duplicate requests.

## Architecture and verification {#verification}

The domain models are technical filing workpapers. Accounting entries and bank
payments remain native `account.move` / payment / reconciliation operations;
this calculation creates none. No public context flag bypasses generated-field
guards. Child facts and filings have active-company rules; accounting users and
managers have explicit native-style ACL. Draft facts may be edited; generated
results, active XML and filed snapshots are protected in both UI and API.
Accounting users read fleet sources; a fleet officer maintains them. Statutory
editions are system-administrator configuration. Same-content storage migration
and download-token generation preserve the exact XML rather than replacing it.

Run Odoo with `--test-enable --test-tags=/l10n_sk_vehicle_tax` and install/upgrade
this module. Tests cover the official 2026 hybrid example (86.95), segment
rounding, multi-page/zero-rate XML, corrections, stale facts, direct API/default
guards, company isolation and an ordinary accounting manager without sudo.
XSD validation is distinct from acceptance by an authority.

## Primary sources and edition maintenance {#sources}

- [Act361/2014, published version effective from2025](https://static.slov-lex.sk/static/SK/ZZ/2014/361/20250101.print.html).
- [MF/017488/2024-726 instructions](https://www.mfsr.sk/files/archiv/71/Poucenie-na-vyplnenie-DP-k-DzMV_v2025_final.pdf).
- [Financial Administration2026 worked examples](https://podpora.financnasprava.sk/335558-Vyp%C3%ADsanie-vyplnenie-da%C5%88ov%C3%A9ho-priznania-r-2026).
- [Original official XSD](https://ekr.financnasprava.sk/Formulare/XSD/dmv2025.xsd)
  SHA256 `d1b154eb027c5d70ed4afaeef85add1612a74674960cfd4665be1cd476502b57`.

Review the law, form and rates for each production year. An open-ended published
edition is not a guarantee against future amendments. Create a new dated
edition when needed; an edition already retained by a calculation is protected.
