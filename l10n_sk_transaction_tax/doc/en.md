---
title: Slovak financial transaction tax
summary: Native ledger sources, reviewed DFT classifications and OZNDFTv26 reporting.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Prepare a corporate self-assessment notice from posted journal items and
retained actual transaction/payment evidence. This module uses the shared
statutory retention and delivery workflow. It does not inherit the dividend
notice and does not replace the native accounting ledger.

## Common case {#common-case}

1. Select the month and a posted foreign-account bank credit, its actual date
   and the evidence for self-assessment grounds c. Review the computed deadline.
2. Review sources, then Post tax to create the native 538/345 liability once.
3. Export XML; the retained payload and exact attachment are frozen together.
4. Record the actual filing and retain its receipt in shared delivery tracking.
   This records a filing, it does not transmit it or prove authority acceptance.

A changed phone, address or ledger after export warns that a correction may be
needed. It does not replace the exported bytes or prevent recording their actual
filing. Posting an already filed notice uses its retained filed payload.

Bank sources must credit the default payment account of a bank journal. Petty
cash is not a bank transfer. Reversed entries and reversal entries cannot become
new payment or tax-credit sources. This module's own provision is not paid tax.
An externally posted provision reversal is reused instead of reversed again.

For a bank batch, mark every part as a batch payment, enter each individual
amount and unique transaction reference, and review all parts. They must sum to
the complete native line. The cap and minimum then apply to each payment; for
example ten payments of 5,000 EUR give 200 EUR, not one 40 EUR cap. An incomplete
batch is refused. Reuse of the bank amount in another filed month remains barred.

## Sources {#sources}

Use the actual bank credit for a transfer/cash withdrawal. A resident payer's
tax base is the whole actual debit, not an expense-deductibility percentage.
Review the actual transaction date independently from a later bookkeeping date.
For foreign currency retain the amount, currency and official ECB/NBS quote
valid for that day. The tax calculation retains the unrounded converted base;
the XML displays the base to cents. The accounting rate can legitimately differ.

Recharged costs refer to the actual payable settlement, including an offset,
and identify each original third-party transaction separately from its repayment.
A single repayment may cover several original transactions. Tax reductions and
other corrections have their own posted tax source and reviewed legal allocation
evidence. Posting a tax liability is not proof that tax was actually paid.

The operator reviews self-assessment grounds c/d/e, exclusions and tax already
collected by a bank; these are not inferred from an IBAN alone. Exempt and
bank-collected sources remain evidence and are not taxed twice. Annual card
usage uses a stable card reference, never a full card number.

## Workflow {#workflow}

An ordinary accountant selects the company/month, preparation and actual/intended
filing day and actual submitting person. The statutory deadline is computed; a calendar reference is optional.
The existing submission-preparer role gives access to delivery/receipt records.
The preparation date cannot follow the filing date. A corrective notice is
available through the computed deadline; an additional one follows it and
retains the discovery date and previous known tax.

Review sources builds a frozen preview. Post tax creates a native 538/345 entry
or 345/538 for a negative result; it does not manufacture a payment/refund.
Repeated posting is idempotent. An unfiled provision can be reversed natively.
A filed correction posts only the difference from actual provisions/reversals
in the chain, not another full liability. Export uses the original pinned XSD.
Record filing retains exact XML/source snapshots and opens shared delivery
tracking; it does not send the notice or claim authority acceptance.

Reset retains filed evidence and accounting history. Changing a filed payload
requires a separate correction. Stored XML can be downloaded without rerunning
today's master-data checks. Same-content storage migration remains available.

## Current validation boundaries {#limits}

XML validation verifies the form structure; it does not prove receipt by the authority. Identified original transactions
share their EUR 40 cap across partial repayments and earlier effective filed
periods. Changing an earlier allocation requires a reviewed amendment of later
notices; Check earlier recharges detects this dependency without rewriting their
filed XML. Excluded recharges retain their reviewed classification.

The accountant records the company's reviewed share of tax already paid by the
original payer, with the receipt and allocation in the source reference. The
native ledger source is the company's own share; the module does not infer a
legal allocation from a third party's total receipt. The same source cannot be
claimed beyond its remaining amount across effective filed periods.

Partial-month dates stay inside the reported month. The published official form
requires the first date to precede the last date; a one-day period needs an
explicit authority/form resolution and is not silently expanded. A foreign
non-IBAN refund uses the company's bank account, SWIFT/BIC and actual branch
name/city/country, rather than inferring the branch country from the BIC.
A complete company-close reconciliation and future vintage 2027 remain open.
The statutory deadline is computed as the end of the next month, moved to the
next working day under Tax Code section 27(4). A date typed by an operator does
not extend the statutory limit; no general discretionary extension is offered.
Late regular notices warn; corrections use the computed deadline.


## Scope {#scope}

Recording a filing after its deadline does not prove that it was actually sent
late. When the retained export claims an on-time filing date but is recorded
later, Odoo posts a receipt-verification warning with both dates. Retain the
actual portal receipt. If a corrective notice was actually filed after the
deadline, prepare an additional notice under section 16 of the Tax Code. The
warning preserves legitimate retrospective recording and the original XML;
it does not certify the entered date or authority acceptance.

A Slovak bank account with only foreign-provider payer grounds also warns:
check whether the domestic bank already collected the tax. A legitimate
domestic special account remains possible, and the warning changes no amount.

OZNDFTv26 supports periods from January 2026. April–December 2025, their
corrections and the 2025 card tax filed in January 2026 need OZNDFTv25 and are
outside this module. Announced repeal from 2027 is not treated as enacted law;
verify the effective law and form before using a future period.

Primary references are the [official form](https://pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.629.html),
[FS FAQ](https://www.financnasprava.sk/sk/aktualne-dan-clo/faq/dan-financne-transakcie)
and the original XSD pinned in `data/SCHEMA_VERSION`.
