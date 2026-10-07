======================================
Slovakia — INTRASTAT-SK (CE / OCA)
======================================

INTRASTAT-SK declaration for Slovakia: a thin country layer on top of the OCA
``intrastat_product`` declaration engine that renders the official Finančná
správa **INTRASTAT-SK INSTAT (instat62)** XML, computed CE-clean.

The OCA engine collects the intra-EU goods movements and computes the grouped
declaration lines; this module hands those lines to the shared
``l10n_cssk_intrastat_base`` INSTAT renderer to produce the fileable XML.

This is the Community / OCA adapter. It is licensed **AGPL-3** because it
depends on (subclasses) the AGPL OCA engine. The shared INSTAT renderer is
AGPL-3 too; the Enterprise variant ``l10n_sk_intrastat_ee`` — which rides Odoo
EE ``account_intrastat`` instead — reuses it because Data Dance s.r.o. owns it
outright and dual-licenses it.

Features
========

* Country adapter on the OCA ``intrastat_product`` declaration engine, CE-clean
  (no Enterprise ``account_intrastat`` dependency).
* Renders the official FS SR INTRASTAT-SK **INSTAT (instat62)** XML via the
  shared ``l10n_cssk_intrastat_base`` renderer.
* Arrivals / dispatches grouped declaration lines computed by the underlying
  OCA engine.
* The INSTAT renderer is shared with the EE variant so both adapters emit the
  identical statutory XML.

Usage
=====

Install alongside the OCA ``intrastat_product`` engine on the Slovak chart.
Create an INTRASTAT product declaration for the reporting period in the OCA
engine, generate / compute its lines, then export the INTRASTAT-SK INSTAT XML
for the Finančná správa portal.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
