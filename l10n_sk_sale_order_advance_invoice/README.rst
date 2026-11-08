========================================
Advance Invoices - Slovak Localization
========================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Slovak chart wiring for advance invoices (preddavkové faktúry)**

Wires the country-neutral ``sale_order_advance_invoice`` module to the Slovak
chart of accounts. On install it configures, for every company on the Slovak
chart template:

* the dedicated tax-documents journal (Faktúry k prijatým platbám),
* the reconcilable advance-clearing account **324001** (created — the standard
  chart has no reconcilable clearing account),
* the short-term received-advance account **324000** (Prijaté preddavky),
* the long-term received-advance account **475000** (Dlhodobé prijaté preddavky).

Existing manual configuration is preserved (only empty fields are filled).

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_sale_order_advance_invoice``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``sale_order_advance_invoice``, ``l10n_sk``

Authors: Data Dance s.r.o.
