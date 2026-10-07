=====================================
SK Corporate Income Tax Return (DPPO)
=====================================

The Slovak country layer for the income-tax framework
(``l10n_cssk_income_tax_base``). It provides the **DPPOv25** form — daňové
priznanie k dani z príjmov právnických osôb (DPPO):

* The full body line set (r100 … r1192) as version data. ``r100`` (výsledok
  hospodárenia pred zdanením) is computed from the P&L; the remaining lines are
  entered by the accountant via the override UI.
* Header mapping from the company (DIČ, IČO, obchodné meno, sídlo, zdaňovacie
  obdobie, typ priznania).
* The official **dppo2025.xsd** is vendored and the XML export is validated
  against it.

Features
========

* DPPOv25 body line set (r100 … r1192) as version data.
* ``r100`` auto-computed from the accounting result; the rest entered by the
  accountant.
* Company header mapping (DIČ, IČO, obchodné meno, sídlo, obdobie, typ priznania).
* XSD-validated XML export against the official ``dppo2025`` schema.

Usage
=====

*Accounting ▸ Reporting ▸ Slovakia ▸ DPPO.* Create a return for the tax period,
review/enter the body lines (r100 is filled from the P&L), then **Export XML** —
the export is validated against ``dppo2025.xsd`` before download.

**Scope note (v1):** the module auto-computes the accounting result and produces
schema-valid XML. The accounting→tax transformation (adjustment lines, loss
deduction, tax credits, minimum tax) is the accountant's domain and is entered
manually; the inter-line computation formulas need accountant validation before
being automated.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
