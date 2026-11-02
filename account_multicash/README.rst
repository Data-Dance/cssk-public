========================
MultiCash Payment Export
========================

Generates **MultiCash payment files** used by Czech banks — Česká spořitelna,
KB, ČSOB, Raiffeisenbank, UniCredit and others — from an OCA
``account.payment.order``. CE-clean: it builds on ``account_payment_order`` and
the shared ``account_cz_bankfile_base`` builders, with **no Enterprise
dependency**.

The file rendering is delegated to ``account_cz_bankfile_base``; this addon only
feeds it the normalized payment items from the payment lines and resolves the
target format from the payment method.

Features
========

* **CFD** — domestic Czech credit transfers and direct debits (inkasa).
* **CFU** — urgent domestic Czech credit transfers.
* **CFA** — foreign (cross-border) payments.
* **MT101** — SWIFT Request For Transfer.
* Variable / Constant / Specific symbol (VS / KS / SS) on every payment line,
  with a fallback that parses a ``VS:`` / ``KS:`` / ``SS:`` token from the
  payment communication when the field is left empty.
* CFA / MT101 require the journal's bank to carry a BIC, otherwise the export is
  blocked with a clear error.
* Registers the matching outbound (and CFD inbound, for inkaso) payment methods.

Usage
=====

Set the bank journal's payment method to the desired MultiCash format
(*MultiCash CFD / CFU / CFA / MT101*). Build a payment order from vendor bills as
usual (*Accounting ▸ Vendor ▸ Payment Orders*), fill the VS/KS/SS symbols on the
lines (or leave them empty to fall back to the communication), confirm the order
and **Generate Payment File** — the format-specific file (``.cfd`` / ``.cfu`` /
``.cfa`` / ``.mt101``) is produced for upload to the bank.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
