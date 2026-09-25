==========================================
Slovakia — Súhrnný výkaz (EC Sales List)
==========================================

Slovak EC sales list on top of ``l10n_cssk_ec_summary_base``. Codes **0** goods
/ **1** triangulation / **2** services, with FS SR ``SDV`` XML export.

Depends on ``l10n_sk`` + the shared framework — no ``account_reports``.

Setup
=====

Tag the intra-EU supply taxes with ``account.tax.cssk_ec_summary_code`` (0 %
intra-community goods → ``0``, services → ``2``). Supplies to EU-registered
customers using those taxes are then aggregated per (country, VAT, code).

Status
======

**Functional.** Aggregation, VIES preflight and the XSD-validated ``SDV`` export
work (verified by a test that posts an intra-EU supply and exports). The XSD /
template element names are a **stand-in** (see the base module) — replace with
the official FS SR schema before live filing. Triangulation (code 1, middle
party only) needs a country override + accountant sign-off.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
