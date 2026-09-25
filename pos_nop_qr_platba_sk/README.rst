====================================
POS — QR Platba (SK) via NOP KVERKOM
====================================

Adds a **Slovak QR Platba** online payment method to the Point of Sale. When the
cashier picks it, the POS mints a NOP KVERKOM transaction id, shows the customer
a *PAY by square* (payme.sk) QR code, and confirms the payment as soon as the
bank pushes the notification to NOP — instant bank-to-bank settlement, no card
terminal.

It builds on ``nop_kverkom_base`` (the mTLS transport and transaction ledger),
on ``pos_online_payment`` (reusing its QR popup and the
``ONLINE_PAYMENTS_NOTIFICATION`` bus channel) and on
``account_qr_code_payme_sk`` (the SBA standard payment-link generator). The QR
content is the Slovak SBA payment-link URL with ``PI=QR-<uuid>`` bound to the
NOP transaction.

Features
========

* New POS online payment method *QR Platba (SK)*, with its own
  ``qr_platba_sk`` payment provider and payment method (created on install).
* Customer-facing **payme.sk QR code** generated from the till's NOP merchant
  IBAN and name; payment in **EUR** only.
* Real-time confirmation: NOP is drained opportunistically on every POS poll, so
  the popup closes automatically the moment the bank notification arrives.
* Configurable cashier timeout (``qr_platba_timeout_seconds``, min 30 s) after
  which the popup shows the red *still no confirmation* prompt — but never
  auto-closes; the cashier always picks the outcome.
* Explicit cashier outcomes: **customer did not pay** (cancel) or **close
  without confirmation**, the latter producing the non-confirmation receipt
  (*doklad o nepotvrdení zrealizovanej platby*) via ``nop_kverkom_base``.

Usage
=====

Configure a till for NOP in ``nop_kverkom_base`` (environment, mTLS certificate,
merchant IBAN/name). Then create or edit a POS payment method, enable *Online
payment*, and attach the *QR Platba (SK)* provider; set the cashier timeout if
needed. At the register, choose the QR Platba method, let the customer scan the
displayed code, and the order is confirmed automatically on the bank push.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
