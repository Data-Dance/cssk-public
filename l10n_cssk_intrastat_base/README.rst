===========================================
CZ/SK Intrastat — INSTAT XML builder (base)
===========================================

Edition-neutral, dependency-free **INSTAT (instat62)** XML builder and validator
for **INTRASTAT-SK**. It renders and validates the official Finančná správa
INTRASTAT-SK message (``intrastat.financnasprava.sk``, schema ``instat62.xsd``
vendored in ``data/``) from a normalized header + line dicts.

It depends on ``base`` only — **no** dependency on the OCA intrastat engine or
Odoo EE ``account_intrastat`` — so nothing in it is bound by OEEL. It is
AGPL-3; Data Dance s.r.o. is its sole owner and dual-licenses it, so the same
builder serves the Community adapter (``l10n_sk_intrastat``) under AGPL-3 and
the Enterprise one (``l10n_sk_intrastat_ee``) under the Data Dance proprietary
licence. There is no UI; this is a shared rendering library.

Features
========

* ``cssk.instat.builder`` (AbstractModel) with two entry points:

  * ``build_instat_xml(header, lines)`` — one declaration / one flow (Community
    adapter).
  * ``build_instat_envelope(env_header, decl_groups)`` — one envelope with
    several declarations, e.g. arrivals + dispatches (Enterprise adapter).

* Both validate the rendered XML against the vendored ``instat62.xsd`` and raise
  on failure.
* Integer coercion of ``netMass`` / ``quantityInSU`` / ``invoicedAmount`` per
  the schema, and normalized Party / Address rendering for the envelope sender
  and each declaration's PSI.

Usage
=====

This module ships no menus or views. The Community / Enterprise INTRASTAT-SK
adapters call ``self.env["cssk.instat.builder"].build_instat_xml(header, lines)``
(or ``build_instat_envelope(...)``) with the normalized header and line dicts
documented in ``models/cssk_instat_builder.py`` and embed the validated XML in
the declaration.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
