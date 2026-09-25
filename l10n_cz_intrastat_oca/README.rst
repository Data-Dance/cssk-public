Czechia — INTRASTAT-CZ (CE / OCA)
=================================

Thin Czech country layer on the OCA ``intrastat_product`` declaration engine.
The engine collects intra-EU goods movements and computes the grouped
declaration lines; this module renders them as the official Celní správa
InstatOnline CSV (the file uploaded at celnisprava.gov.cz → InstatOnline) via
the shared ``l10n_cssk_intrastat_base`` renderer.

The CSV column layout, constant fields and number formatting reproduce the
official Odoo EE ``l10n_cz_intrastat`` output (validated against its expected
file in the shared base's tests). The Czech declaration has no XSD — the
InstatOnline portal validates on upload.

This is the Community/OCA adapter; it is intentionally NOT named
``l10n_cz_intrastat`` to avoid colliding with Odoo Enterprise's native module
of that name. One edition installs exactly one of the two.

Features
========

* Subclasses the OCA ``intrastat.product.declaration`` engine and adds only the
  Czech file output, leaving gathering and computation to OCA.
* Produces the official Celní správa InstatOnline CSV for upload at
  celnisprava.gov.cz → InstatOnline.
* Maps the engine's computed declaration lines onto the shared CSV renderer in
  ``l10n_cssk_intrastat_base`` (partner VAT, country, origin country,
  transaction/transport/Incoterm codes, CN8, weight, supplementary units and
  company-currency value).
* Single-direction declarations: arrivals are written as ``A``, dispatches as
  ``D``.
* The attachment is written with a ``.csv`` extension, since the Czech
  declaration is filed as a CSV, not XML.
* Output reproduces the official Odoo EE ``l10n_cz_intrastat`` layout, constant
  fields and number formatting.

Usage
=====

Install this module for a Czech company. Create and compute an INTRASTAT
declaration using the standard OCA ``intrastat_product`` workflow, then generate
the declaration file: for Czech companies the module produces the InstatOnline
CSV and attaches it with a ``.csv`` name. Upload the resulting file at
celnisprava.gov.cz → InstatOnline, where the portal validates it on upload (the
Czech declaration has no XSD).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
