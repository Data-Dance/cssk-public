======================
KB BEST Payment Export
======================

Generates Komerční banka **BEST** payment files from an OCA
``account.payment.order`` — CE-clean, no Enterprise dependency. Upload the file
in MojeBanka Business, Profibanka or Přímý kanál. The record layout, the rules
the builder enforces and the specification it follows are described in
``account_kb_best_base``.

Payment methods
===============

* **KB BEST (domestic transfer)** — úhrady, record ``01``.
* **KB BEST (domestic direct debit / inkaso)** — the same record with
  operation code ``1``, on an inbound payment order.
* **KB BEST (foreign / SEPA transfer)** — record ``02`` with the ``03``
  structured address. A payment that qualifies (EUR, IBAN in a SEPA country,
  shared charges) is flagged SEPA; anything else goes as a standard foreign
  payment.

Usage
=====

Create a payment mode with one of the methods above and the KB bank journal,
build the payment order from vendor bills as usual, fill VS/KS/SS on the lines
(or leave them empty to take a ``VS:`` token from the communication), confirm
and **Generate Payment File**. The file is ``BEST-DP-…ikm`` (domestic) or
``BEST-ZP-…ikm`` (foreign).

The journal's account must be at KB (bank code ``0100``). The account
currency is the journal's (or the company's); a domestic payment in another
currency is sent with KB's conversion flag.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
