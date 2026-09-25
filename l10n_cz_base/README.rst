=================================
Czech Republic Base Localization
=================================

This module provides the Czech-specific building blocks shared by other
modules (for example ISDOC e-invoicing). It is kept deliberately lightweight
and depends only on the ``account`` module.

It adds two things: bidirectional conversion between a Czech IBAN and the
legacy domestic "prefix-number/bankcode" account number on
``res.partner.bank``, and the Variable / Constant / Specific symbol fields
(VS / KS / SS) on ``account.move``.

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
* ``account.move``: Variable symbol (VS), Constant symbol (KS) and Specific
  symbol (SS) fields. The Variable symbol is computed (digits only) from the
  invoice number for customer documents and from the reference for vendor
  documents, and remains editable.

Usage
=====

* Open a partner's bank account (``res.partner.bank``). Enter the IBAN in the
  account number field; the Bank Code, Legacy Account Starting Number and
  Legacy Account Number fields are filled automatically from it.
* On an invoice or other journal entry (``account.move``) the Variable symbol
  is proposed automatically from the document number (or vendor reference) and
  can be overridden. Fill the Constant and Specific symbols as needed.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
