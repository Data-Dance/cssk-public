==========================================
CZ/SK VAT Return — Shared Framework
==========================================

Country-neutral engine behind the Slovak **daňové priznanie k DPH** (DPHv25)
and Czech **DPHDP3**. Numbered lines (riadky) computed from **tax tags** +
aggregate formulas.

**CE-clean:** uses ``account.account.tag._get_tax_tags`` (Odoo CE), not the EE
``account_reports`` engine.

Architecture
============

* ``cssk.vat.return.version`` — line definitions + template + schema + types.
* ``cssk.vat.return.line.def`` — ``tags`` (formula e.g. ``-03``; leading ``-``
  is the sign), ``aggregate`` (formula over codes, e.g. ``r04 + r06``), or
  ``manual``.
* ``cssk.vat.return`` — mail.thread; compute (the evaluator) + XSD-validated
  XML export.

Engine support
==============

Implements the **tags** and **aggregate** engines, which cover the output/input
tag lines and total aggregations. Odoo's own DPH report additionally uses
``sum`` (children roll-ups) and custom ``calcul`` / external engines for some
net-payable lines — those need extended engine support or ``manual`` entry, and
accountant validation.

Status
======

**Functional.** The evaluator is verified against real SK tags (a posted 23 %
sale → base 1000 / tax 230 / aggregate 1230). Country modules ship the line
definitions, template and schema.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
