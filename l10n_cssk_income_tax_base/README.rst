===================================
CZ/SK Income Tax Return — framework
===================================

The shared, country-neutral engine for the corporate income-tax return (DPPO),
mirroring the VAT-return and financial-statement frameworks. It depends on Odoo
core only (``account`` + ``mail`` + ``l10n_cssk_core``), so it is
Community-clean and runs on Odoo 18.0 and 19.0.

The country layer (e.g. ``l10n_sk_dppo``) supplies the actual line set, the
header mapping and the official schema. The accounting→tax transformation (the
adjustment lines) is the accountant's domain — this framework auto-computes the
accounting result and the formulaic spine and takes the rest as manual entry.

Architecture
============

* ``cssk.income.tax.version`` + line definitions — line kinds: ``account``
  (P&L / accounting result before tax), ``aggregate`` (the tax-computation
  spine, a formula over line codes) and ``manual`` (accountant adjustments —
  připočitatelné / odčitatelné položky); plus the submission types
  (``cssk.income.tax.type``). New legislation ships as a new version record.
* ``cssk.income.tax.return`` (mail.thread) — the return aggregate. Evaluator,
  manual overrides preserved and fed into dependent aggregate lines on
  recompute, state machine (draft → submitted), amendment (dodatečné /
  opravné), XSD-validated statutory XML export, and an optional income-tax
  provision posting (591/341).
* A wizard to generate a return for a period + version.

Features
========

* Versioned line definitions per country and statutory form, with three line
  kinds (accounting result, formulaic aggregate, manual adjustment).
* Manual overrides that survive recompute and propagate into dependent
  aggregate lines.
* XSD-validated statutory XML export and a submission state machine with
  amendment support.
* Optional income-tax provision journal entry (post / reverse).

Usage
=====

*Accounting ▸ Reporting ▸ Income Tax (DPPO).* Use **Generate** to create a
return for a period and version; the accounting result and the formulaic spine
are computed automatically. Open the return, enter the manual adjustment lines,
**Compute** to refresh the aggregates, then **Export XML** for submission.
Optionally post the income-tax provision.

Wizards
=======

* **Generate Income Tax Return** (*Accounting ▸ Reporting ▸ Income Tax (DPPO) ▸
  Generate*) — pick the company, version, submission type and the period
  (date from / date to); it creates the ``cssk.income.tax.return``, computes the
  lines and opens the new return. The period end must be on or after the start.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
