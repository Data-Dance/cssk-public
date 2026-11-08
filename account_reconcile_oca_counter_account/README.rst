=================================================
Reconcile OCA — show the counterparty's account
=================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Put the counterparty bank account back on the OCA bank statement reconciliation screen.**

OCA's reconciliation widget renders a curated set of fields, and
``account_number`` — the counterparty's account as the bank sent it — is not
among them. Every statement importer in the
``account_statement_import_base`` family fills that field, so the information is
there; it is simply invisible on the one screen where somebody is deciding who a
payment came from.

In CZ/SK that matters more than elsewhere. A payer who quotes no variable symbol
is very often identifiable only by their account number, and matching by name
alone is exactly the guess that puts a receivable against the wrong customer.

This module adds ``account_number`` and ``partner_bank_id`` to the reconciliation
form. Nothing else — no fields, no logic.

It is deliberately generic: it names no bank, so it serves the Tatra banka and
Fio banka importers, the GPC file importer and anything else in that family
equally. Worth proposing upstream.

.. rubric:: Module facts

- **Technical name:** ``account_reconcile_oca_counter_account``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``account_reconcile_oca``

Authors: Data Dance s.r.o.
