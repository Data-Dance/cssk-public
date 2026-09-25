==========================================
AI Invoice Extraction (vyťažovanie faktúr)
==========================================

Autonomous accounts-payable pipeline: supplier invoice PDFs in, **draft** vendor
bills out, with the source document and the model's raw output kept for audit.

How it works
============

1. **Ingest** — a PDF arrives on the vendor-bill email alias, or is uploaded.
2. **Extract** — the model is given the PDF and a forced tool call, and returns
   **natural keys only**: supplier VAT, ISO currency, dates, amounts, the per-rate
   VAT breakdown, a reverse-charge hint.
3. **Resolve** — plain Python maps those keys onto Odoo records: supplier by VAT,
   domestic VAT rate → tax through the company's rate map, fiscal position drives
   the reverse-charge / intra-EU remap, duplicate detection, sanity gates.
4. **Create** — always a **draft** ``account.move``, never a posted one.

The split is the point: *the model is never asked to pick an Odoo record.* It
returns keys a human could verify by looking at the page, and Python resolves
them. A wrong answer therefore shows up as a failed reconciliation or a parked
review, not as a silently mis-posted bill.

Anything that does not reconcile — net + VAT ≠ gross, a VAT breakdown that does
not sum to the totals, confidence below the company threshold — is parked in
*Needs Review* rather than guessed at.

Scope
=====

Country-neutral. The Slovak and Czech specifics live in the fiscal positions and
in the VAT-rate → tax map, not in this module. It is the Community answer to Odoo
Enterprise's IAP-based ``account_invoice_extract``, and the *vyťažovanie došlých
faktúr* component of the CZ/SK localization.

Configuration
=============

*Settings ▸ Accounting ▸ AI Invoice Extraction*: provider and model (from
``muk_ai``), target journal, fallback expense account, confidence threshold,
whether to auto-create partners and bank accounts, the reverse-charge rate, and
the VAT-rate → tax map. A disabled cron (*AI Invoice: process pending
extractions*) sweeps pending extractions every 5 minutes once enabled.

Cost is recorded per run — input/output tokens and USD — and totalled per
extraction, so the spend is visible rather than inferred.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
