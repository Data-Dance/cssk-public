---
title: Slovak withholding tax notice
summary: Resident dividends and author income, actual settlements, OZN4311v26 and Annex A.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Prepare a complete monthly resident withholding notice from the company's
existing accounting and actual payment evidence. The module does not book a
second dividend, author expense, payment or tax. It uses the shared statutory
export, retained filing and receipt workflow.

## Common case {#common-case}

1. Select the company/month, actual preparation/filing dates, preparer and
   withholding account 342. Confirm that no other resident withholding titles
   are missing: row 01 must include all resident withholding for the month.
2. Add the dividend recipient, completed profit period, actual decision and
   payment dates, gross amount and source references. Select the posted income,
   payment and withholding lines. Review the actual payment evidence.
3. Allocate the separate actual tax transfer: its 342 debit, amount, actual
   date and evidence. A posting or transfer request does not prove payment.
4. Review sources, then Export XML against the original pinned XSD. Record the
   external filing and retain its receipt through shared delivery tracking.
   This records an external action; it does not transmit or prove acceptance.

The existing Statutory submissions: prepare role gives an ordinary accountant
receipt access without system or accounting-manager rights. An unfiled preview
can be reset. Reopening filed history retains the shared manager gate.

## Sources and payment forms {#sources}

Use dividend liability 364, author liability 321/379 and withholding/remittance
342, including valid analytics. Actual dates can differ from bookkeeping dates.
Reversed sources and reversal entries are refused. All live notices reserve
their source amounts across months; a full correction replaces its predecessor
without creating another payment. A working correction cannot release the
still-filed allocation for an unrelated notice. Concurrent source changes retry.

Bank/cash payments and native account.payment through its outstanding account
are supported. A registered payment still needs reviewed actual-payment
evidence; a generic current-asset credit is insufficient. Select Set-off for
income paid by mutual claims: retain the legal set-off evidence and reconcile
the recipient's actual receivable. Tax remittances have their own bank or
documented authority-allocation source. The source snapshot retains the actual
settlement credits and native payment/claim references. A combined entry with
gross liability, withholding and net payment is supported; the same physical
credits cannot prove more reported payments than they actually settle.

The independent [FS example](https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_006_PO_2026_IM_podiel_zisk.pdf)
checks 650 + 1,050 = 1,700. Dividend rates follow the start of the profit period:
10% for 2024 and 7% for other supported periods. Resident author income without
an advance written waiver uses 19%. A section 43(14) waiver is reported through
its separate agreement notice, not a fictitious zero withholding here.

For author income, Taxable income means income excluding VAT less an art-fund
contribution only if that contribution was actually withheld, as required by
[section 43(5)(b)](https://www.financnasprava.sk/sk/podnikatelia/dane/dan-z-prijmov/fyzicke-osoby/slobodne-povolania).
Keep the original remuneration, any actual contribution and their ledger
evidence. Do not subtract an assumed contribution. The author's payment then
equals this taxable income less withholding tax.

Original author bills and separate, single-recipient liability journals support
linked partial credits. The adapter reads currently posted native credits whose
document date is effective by the actual payment date. A native reversal of a
credit can restore capacity. Draft credits do not reduce it. Invoice/refund and
journal reversal links must match their source type, company, payable account
and recipient.

For a 1,500 remuneration and a 150 credit before payment, with no VAT or actual
art-fund deduction, the remaining income is 1,350, withholding is 256.50 and the
net payment is 1,093.50. Each original payable line keeps its own limit; all
instalment lines also share the reduced source limit across months and notices.
A full correction replaces its predecessor rather than consuming it again.
The same checks include old retained snapshots without the new pool metadata.

Source capacity is an upper bound, not proof of payment or the tax base. Enter
the reviewed actual taxable payment and retain its bank/set-off and deduction
evidence. A later credit does not automatically rewrite an earlier actual
payment or its filing. Account for a real refund separately and review the
correction's tax period before preparing it. Compound or multiple-recipient
journals keep their existing source policy; do not invent a proportional split,
unlink credits or rewrite posted accounting to bypass a source check.

## Filing, deadlines and corrections {#filing}

Only remittances through the actual filing cutoff are included. Multiple dates
remain individually retained. Annex A prints one remittance date per income;
the accountant reviews that presentation from the actual dates.

Regular filing warns after the following month's 15th, shifted for days of rest.
The September 2026 exception and Easter are respected. A different date granted
by the authority under section 43(11) requires its actual retained decision.

The exact exported XML and payload are the filing record. Later changes to the
ledger or recipient's address warn about a possible separate correction; they
do not block recording the external filing. Allocation consumption is rechecked.
Later working drafts do not displace an already exported allocation when its
actual filing is recorded. Creating another export still checks all working
reservations, as well as retained claims from other notices.
Create correction copies the complete income set and retains the predecessor.
Confirm its actual filing date against a receipt, not a planned cutoff or the
time Odoo recorded it. Filed ownership and correction identity survive reset.

## Identity and scope {#scope}

Formal Slovak birth-number checks cover length, embedded date, payment boundary
and mod11. Nine digits refer to a birth before 1954; the two-digit year alone
does not imply 2000. Formal validity does not prove assignment. An identifier
inconsistent with section 2 of 301/1995 requires authority verification under
section 7; do not invent a replacement. Date of birth is used only when no Slovak
birth number is assigned.

Supported: a Slovak corporate EUR payer, resident individual dividends from
profit periods starting in 2017 or later and resident author income without a
waiver. Other resident withholding titles require a complete notice outside
this adapter; the scope confirmation prevents silently omitting them. Foreign
recipients/Annex B, legal-person recipients and pre-2017 dividend health regimes
are outside this adapter. OZN4311v26 does not certify a future form vintage.
The [official form](https://pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.626.html)
and original schema bytes are pinned in data/SCHEMA_VERSION. Signature and
transport are separate integrations.
