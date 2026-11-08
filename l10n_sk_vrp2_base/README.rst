=================================
Slovak VRP2 - Base / Connection
=================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Connection layer for the Slovak Virtual Cash Register (VRP 2)**

Base module for integrating Odoo with the Slovak Financial Administration's
Virtuálna registračná pokladnica 2 (VRP 2) REST API.

Provides the shared communication layer:
- ``vrp2.client`` API client with crpChecksum request signing
- VRP2 credentials, session and dashboard cache on the company
- VRP2 VAT-rate ↔ Odoo sales-tax mapping
- Login / Logout actions in the Accounting settings

Functional modules (invoice payments, POS receipts, ...) depend on this
module and reuse ``vrp2.client``.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_vrp2_base``
- **Version:** 18.0.2.3.0
- **Licence:** AGPL-3
- **Requires:** ``account``

Authors: Data Dance s.r.o.
