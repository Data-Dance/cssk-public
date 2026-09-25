==========================================
CZ/SK EC Sales List — Shared Framework
==========================================

Country-neutral engine behind the Slovak **Súhrnný výkaz** and Czech
**Souhrnné hlášení** (EC sales list). One aggregated line per (member-state,
customer VAT, transaction code); country modules ship codes + template + XSD.

Depends on Odoo core only (``account``, ``mail``, ``l10n_cssk_core``).

Architecture
============

* ``cssk.ec.summary.statement.version`` — versioned template + schema + types.
* ``cssk.ec.summary.statement`` — mail.thread; draft → preview → exported →
  submitted; ``action_compute_lines`` + ``action_export_xml`` (VIES preflight →
  QWeb render → XSD validate → attach).
* ``cssk.ec.summary.statement.line`` — the aggregated line.
* ``account.tax.cssk_ec_summary_code`` — marks intra-EU supply taxes (the code
  drives the line's transaction type).
* Move-line hooks: ``_cssk_ec_transaction_code`` / ``_cssk_ec_amount`` /
  ``_cssk_ec_partner_vat`` (country-overridable).

Status
======

**Functional skeleton.** Aggregation, VIES preflight (presence/format — wire a
real VIES network check for live filing) and the XSD-validated export pipeline
work. Eligibility is driven by tagging the intra-EU supply taxes with
``cssk_ec_summary_code`` (a deployment step). Triangulation (middle-party only)
is a documented TODO.

Pending validation by CZ/SK accountants.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
