==========================
Fio banka — payment orders
==========================

Builds Fio XML payment orders on the OCA ``account.payment.order`` and sends them
to the bank over the API.

Why Fio's own XML
=================

It is the only upload format that carries **KS / VS / SS as real elements**.
``pain.001`` is EUR-only and ABO is CZK-domestic-only, so on either of those the
symbols have to be smuggled through free text.

Three kinds of order, chosen per line:

* a Czech account (CZ IBAN, or ``[prefix-]account/bank``) → ``DomesticTransaction``,
  which also carries a foreign-currency transfer between Fio accounts;
* EUR to a SEPA IBAN → ``T2Transaction`` (Europlatba);
* anything else → ``ForeignTransaction``, where the beneficiary's address, the
  BIC, a payment reference, the charge bearer and the platební titul are all
  mandatory.

Problems are collected and reported together, at confirmation time, instead of
one ``UserError`` per attempt.

Send to Fio
===========

The button uploads the generated file and records what the bank answered. It
works out the format from the file itself, so it also sends the ABO file from
``account_abo`` and the pain.001 from ``account_banking_sepa_credit_transfer`` —
those exporters become Fio-capable with no new format code.

**"Sent" is not "paid".** Fio stores the orders as an *unauthorised batch*;
somebody with signing rights still has to confirm it in internet banking with an
SMS or a Fio signature. Nothing in Odoo can move money on its own.

If an upload's answer is lost in transit
========================================

The order goes to **Unknown**, never back to *Not sent*. The bank may be holding
the batch, and a retry would create a second one — authorise both and every
payment goes out twice.

Two buttons record what the operator actually saw in internet banking. Only *It
is NOT in the bank* re-enables sending.

Known limitations
=================

* Fio's ``idInstruction`` is the **batch** number. The instruction id that later
  appears on statement lines is a different number, so a payment order cannot be
  linked back to its statement lines through it — match on VS, amount and date.
* ``accountFrom`` is a plain number (``16n``) and cannot express an account
  prefix; a journal whose account has one is refused with an explanation.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
