=======================================================
Czech EET 2.0 - Point of Sale gift cards and eWallets
=======================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Report gift-card / eWallet top-ups and redemptions in the EET 2.0 drawdown fields (urceno_cerp_zuct / cerp_zuct).**

.. _czech-eet-20--pos-gift-cards-and-ewallets-l10n_cz_eet2_pos_loyalty:

Czech EET 2.0 — POS gift cards and eWallets (``l10n_cz_eet2_pos_loyalty``)
==========================================================================

Bridge between ``l10n_cz_eet2_pos`` and ``pos_loyalty``. Installs itself when both are present. Odoo 17.0.

Why
---

A gift card or eWallet is a *prostředek k platbě v omezené síti* (§ 5 odst. 1 písm. e) zákona č. 180/2026 Sb.). The Financial Administration (Q&A 585, 584; "Popis položek datové zprávy", ch. 13–14) requires **both** the top-up and **every** redemption to be recorded when they happen at the till, and the data message has two dedicated fields for them:

+-----------------------------------------+----------------+----------------------+---------------+
| Event                                   | ``celk_trzba`` | ``urceno_cerp_zuct`` | ``cerp_zuct`` |
+=========================================+================+======================+===============+
| Top-up 1 000 Kč + drink 50 Kč paid cash | 1 050          | 1 000                | —             |
+-----------------------------------------+----------------+----------------------+---------------+
| Redemption of 300 Kč                    | 300            | —                    | 300           |
+-----------------------------------------+----------------+----------------------+---------------+

Odoo books a redemption as a negative reward line, so the order's ``amount_total`` is only what was paid on top of the card. Without this module the top-up went out as a plain sale and the redemption was simply under-reported (or, for an order settled entirely by card, not reported at all because no payment line existed).

What it does
------------

- Top-up lines (products of a gift-card / eWallet program active in the POS, not reward lines) → ``urceno_cerp_zuct``.
- Redemption reward lines of those programs → ``cerp_zuct``, and the same amount is added back to ``celk_trzba``.
- An order with a redemption is in scope even when it carries no payment line.

A *voucher for one specific good or service* (FS Q&A 585, type 2) is not a limited-network instrument: its sale is a plain sale and its redemption is not a payment. Model such vouchers as ordinary products, not as gift cards.

Configuration
-------------

None. Amounts follow the base module's CZK conversion.

.. rubric:: Module facts

- **Technical name:** ``l10n_cz_eet2_pos_loyalty``
- **Version:** 17.0.1.0.1
- **Licence:** AGPL-3
- **Requires:** ``l10n_cz_eet2_pos``, ``pos_loyalty``

Authors: Data Dance s.r.o.
