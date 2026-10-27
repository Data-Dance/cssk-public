=================================
Czech Republic Base Localization
=================================

This module provides the Czech-specific building blocks shared by other
modules (for example ISDOC e-invoicing). It is kept deliberately lightweight
and depends only on ``account`` and ``l10n_cssk_payment_symbols``.

It adds bidirectional conversion between a Czech IBAN and the legacy domestic
"prefix-number/bankcode" account number on ``res.partner.bank``. The Variable /
Constant / Specific symbols (VS / KS / SS) are owned by
``l10n_cssk_payment_symbols``; this module only keeps their old field names
(``variable_symbol``, ``constant_symbol``, ``specific_symbol``) as aliases for
code written against them.

Features
========

* ``res.partner.bank``: the legacy account number, account prefix
  (předčíslí) and four-digit bank code are stored fields **computed from the
  IBAN**, which stays the primary storage format. The IBAN is split following
  the CNB layout (bank code, prefix, account number); leading zeros are
  stripped from the legacy representation.
* ``res.partner.bank``: helper methods build a valid Czech IBAN (ISO 13616
  mod-97 check digits) from legacy parts and convert a legacy
  "prefix-number/bankcode" string to an IBAN, so input from external
  documents can be normalised to IBAN.
* ``account.move``: ``variable_symbol``, ``constant_symbol`` and
  ``specific_symbol`` — stored, writable aliases of the
  ``l10n_cssk_payment_symbols`` fields, kept for one release so ISDOC and
  customer code written against the old names keep working.

Usage
=====

* Open a partner's bank account (``res.partner.bank``). Enter the IBAN in the
  account number field; the Bank Code, Legacy Account Starting Number and
  Legacy Account Number fields are filled automatically from it.
* The payment symbols on invoices are described in
  ``l10n_cssk_payment_symbols``.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
