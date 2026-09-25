==========================
CZ Invoice (statutory PDF)
==========================

The Czech country layer that adds the statutory invoice content to Odoo's
invoice, on top of core and ``l10n_cz`` (which already prints the IČO and the
trade-registry line). It supplies the customer DIČ, the Czech payment symbols
and the mandatory statutory phrases (domestic reverse charge §92a, exemptions
§64/§66) on the printed invoice.

Features
========

* Prints the customer **DIČ** next to the IČO / DIČ DPH that the core CZ layer
  already shows (sourced from ``l10n_cssk_core``).
* Adds the Czech **payment symbols** to the invoice information row —
  variabilní symbol, konstantní symbol and specifický symbol.
* Auto-detects and prints the **statutory phrases** required on the invoice:
  domestic reverse charge (§92a), intra-Community supply / exempt (§64) and
  export (§66).
* A per-tax **CZ reverse charge (§92a)** flag drives the §92a phrase, with a
  distinct name so it does not collide with the same-purpose field another
  CZ localization ships (that one is honoured too when it is installed).
* A free-text **manual legal note** that is printed in addition to any
  auto-detected phrase.

The phrase auto-detection (zero-rate + partner country + the per-tax §92a flag)
is a best-effort heuristic — have an accountant confirm the mapping.

Usage
=====

Install the module on a Czech company. On customer invoices the customer DIČ
and any populated payment symbols appear automatically on the PDF. Tick **CZ
Reverse Charge phrase (§92a)** on the relevant tax to print the §92a phrase;
the §64 and §66 phrases are derived from the zero-rate taxes and the customer's
country. Type any extra wording in **Invoice Legal Note (manual)** on the
invoice to have it printed as well.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
