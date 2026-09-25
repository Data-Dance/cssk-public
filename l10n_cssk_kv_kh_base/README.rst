============================================
CZ/SK Control Statement — Shared Framework
============================================

Abstract engine behind the Slovak **KV DPH** and Czech **KH DPH** VAT control
statements. Country modules plug in concrete section sets.

Depends on **Odoo core only** (``account``, ``mail``, ``l10n_cssk_core``) —
no ``account_reports`` — so it is Community/Enterprise- and 18.0/19.0-clean.

Architecture
============

* ``cssk.control.statement.version`` — versioned template + section registry +
  submission types + threshold. New legislation = new version record.
* ``cssk.control.statement`` — the statement (mail.thread; draft → preview →
  exported → submitted), with ``action_compute_lines`` and ``action_export_xml``
  (QWeb render + ``lxml`` root-element check + XSD validation).
* Row mixins: ``...section.mixin`` (detail), ``...summary.mixin`` (aggregated),
  ``...reconciliation.mixin`` (fixed lines, e.g. CZ section C).
* ``account.move.line.cssk_control_section_code`` — stored, computed by a
  country-overridable ``_cssk_resolve_section_code`` (**reverse charge first**).
* ``account.tax`` — ``cssk_control_section_default`` + ``cssk_control_is_reverse_charge``.
* ``account.journal`` — section override.

Status
======

**Skeleton.** Models, mixins, statement lifecycle, wizard, views and the XML
export pipeline scaffold are in place. To do in the country modules / next pass:

* Concrete section models + ``_populate_for_statement`` logic.
* The real ``_cssk_resolve_section_code`` decision trees (SK / CZ).
* ``_cssk_signed_balance`` / ``_cssk_tax_amount`` / ``_cssk_tax_rate`` refinement
  (sign handling for refunds, multi-rate, FX at supply date).
* QWeb XML templates + XSDs per version.

Pending validation by CZ/SK accountants.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
