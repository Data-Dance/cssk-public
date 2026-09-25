================
NOP KVERKOM Base
================

Transport layer for **Slovak QR Platby** through the National Operator of
Payments (NOP), operated by KVERKOM, for instant bank-to-bank payments. The
module provides the mTLS REST client and the authoritative transaction ledger;
it carries **no Point of Sale or invoicing logic** of its own — POS and invoice
integrations are delivered by separate modules that depend on this one.

Each ``pos.config`` is bound 1:1 to one NOP *pokladnica* (cash register), as the
Slovak eKasa framework requires: one mTLS client certificate identifies one
physical till. The certificate's subject (VATSK and POKLADNICA id) is parsed
automatically, and separate certificate slots are kept for the Integration and
Production NOP environments.

Features
========

* ``pos.config`` extension holding the NOP identity (VATSK, POKLADNICA id,
  environment), the merchant IBAN/name, and per-environment mTLS material
  (client certificate, private key, CA bundle).
* ``nop.transaction`` — the authoritative ledger of payment notifications
  received from the bank through NOP, with a full state machine (draft, pending,
  received, confirmed, mismatch, cancelled, expired, refund pending, refunded …).
* ``NopClient`` service — an mTLS-authenticated REST client wrapping
  ``generateNewTransactionId``, ``getAllTransactions`` and
  ``getTransactionHistory``.
* Data-integrity hash verification (SHA-256 of IBAN|AMOUNT|EUR|endToEndId);
  notifications whose hash or amount does not match are flagged ``mismatch``.
* Rate-limited polling (``FOR UPDATE SKIP LOCKED`` so concurrent pollers do not
  stampede the NOP API) plus a safety-net cron that drains pending transactions.
* Non-confirmation receipt report on ``nop.transaction`` for tills closed
  without a bank confirmation.

Usage
=====

Open *Accounting ▸ Configuration ▸ NOP KVERKOM* to review the transaction
ledger and the *Refunds owed* list. Configure a till on its **Point of Sale ▸
Configuration** record: pick the NOP environment, upload the eKasa client
certificate/key/CA for that environment, and select the merchant IBAN. The
VATSK and POKLADNICA id are extracted from the certificate automatically. Install
a dependent module (e.g. ``pos_nop_qr_platba_sk``) to expose the actual QR
payment flow.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
