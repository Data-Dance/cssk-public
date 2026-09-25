==========================
SK Invoice (statutory PDF)
==========================

Turns Odoo's generic invoice into a Slovak ``faktúra`` that carries the
mandatory content of **§74 of the Slovak VAT Act**, on top of what core +
``l10n_sk`` already render (IČO, trade-registry entry, delivery date, VAT
breakdown, PAY by square QR, signature).

It depends on ``l10n_sk``, the shared ``l10n_cssk_core`` and
``l10n_cssk_payment_symbols``.

Features
========

* **Party identifiers** — prints the customer **DIČ** next to the IČ DPH / IČO
  that core already shows.
* **Payment symbols** — variabilný / konštantný / špecifický symbol, sourced from
  ``l10n_cssk_payment_symbols``.
* **Statutory phrases** — auto-detected and printed in Slovak (with an English
  gloss): domestic reverse charge (*prenesenie daňovej povinnosti*, §69/12),
  intra-EU supply (§43) and export (§47) exemptions; plus a free-text manual
  note for edge cases.
* **Language-driven labels** — Slovak for SK-language partners, English
  otherwise, via standard Odoo translations. The statutory phrases always carry
  Slovak because the law requires it.

Usage
=====

Install the module; the Slovak invoice layout is applied to customer invoices.
A per-tax reverse-charge flag and a manual statutory-note field are exposed on
the tax and invoice forms (Accounting). Print the invoice to obtain the §74
``faktúra`` PDF.

**Note:** the phrase auto-detection is a best-effort heuristic (zero-rate +
partner country + the per-tax reverse-charge flag). Have an accountant confirm
the mapping for your tax setup; the manual note field covers edge cases.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
