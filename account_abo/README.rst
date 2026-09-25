==================
ABO Payment Export
==================

Generates **ABO payment-order files** used by Czech (and Slovak) banks — Česká
spořitelna, ČSOB, KB, MONETA, Raiffeisenbank, UniCredit and others — from an OCA
``account.payment.order``. CE-clean: it builds on ``account_payment_order`` and
the shared ``account_cz_bankfile_base`` builders, with **no Enterprise
dependency**.

The module exports domestic credit transfers (úhrady, ABO data type 1501). The
actual file rendering is delegated to ``account_cz_bankfile_base``; this addon
only feeds it the normalized payment items from the payment lines.

Features
========

* Export of credit transfers (úhrady, ABO data type 1501) as a payment file on
  an OCA ``account.payment.order``.
* Batch (hromadný) record arrangement — the orderer account sits in the group
  header.
* Variable / Constant / Specific symbol (VS / KS / SS) on every payment line,
  with a fallback that parses a ``VS:`` / ``KS:`` / ``SS:`` token from the
  payment communication when the field is left empty.
* Per-line symbol validation: numeric only, VS/SS up to 10 digits, KS up to 4.
* Output encoding WIN-1250 with an ASCII fallback.
* Registers an ``ABO`` outbound payment method.

Usage
=====

Set the bank journal's outgoing payment method to **ABO (Czech/Slovak credit
transfer)**. Build a payment order from vendor bills as usual
(*Accounting ▸ Vendor ▸ Payment Orders*), fill the VS/KS/SS symbols on the lines
(or leave them empty to fall back to the communication), confirm the order and
**Generate Payment File** — the ``.abo`` file is produced for upload to the
bank.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
