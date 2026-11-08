======================
POS VRP2 Integration
======================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Integrate Odoo POS with Slovak Virtual Cash Register (VRP 2)**

Integrates Odoo Point of Sale with the Slovak Financial Administration's
Virtual Cash Register 2 (Virtuálna registračná pokladnica 2).

Calls the VRP2 REST API at vcrp.financnasprava.sk to:
- Authenticate and manage sessions
- Synchronise products and categories
- Create fiscal receipts (pokladničné doklady)
- Handle deposits, withdrawals, invoice payments
- Manage closures and reports

.. rubric:: Module facts

- **Technical name:** ``pos_vrp2``
- **Version:** 18.0.4.6.0
- **Licence:** AGPL-3
- **Requires:** ``point_of_sale``, ``l10n_sk_vrp2_base``

Authors: Data Dance s.r.o.
