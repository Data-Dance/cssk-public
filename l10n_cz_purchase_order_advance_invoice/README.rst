============================================
Czech Republic — Received Advance Invoices
============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Czech chart wiring for purchase_order_advance_invoice.**

Wires the statutory Czech accounts and journal for the received
advance-invoice flow: creates the reconcilable clearing account **314001**,
maps net paid advances to **314000** and creates the **PDADV** purchase
journal for the suppliers' tax documents on sent payments.

.. rubric:: Module facts

- **Technical name:** ``l10n_cz_purchase_order_advance_invoice``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``purchase_order_advance_invoice``, ``l10n_cz``

Authors: Data Dance s.r.o.
