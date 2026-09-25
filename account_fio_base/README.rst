=========================================
Fio banka API — shared client and formats
=========================================

The single source of truth for the Fio banka REST API. Reference documentation:
*FIO API BANKOVNICTVÍ*, version 1.9 of 16 October 2025
(https://www.fio.cz/docs/cz/API_Bankovnictvi.pdf). Section numbers in the code
refer to it.

Everything that talks to Fio builds on this module, so the protocol exists once:

* ``account_fio`` — the connection object (token, throttle, expiry)
* ``account_statement_fio`` — movement and official-statement pulling
* ``account_payment_fio`` — Community, OCA ``account.payment.order``
* ``account_payment_fio_batch`` — Enterprise, ``account.batch.payment``

There are **no Odoo models** here — only pure helpers, imported via
``odoo.addons.account_fio_base.utils.*``.

Features
========

``utils.client.FioClient``
    The REST calls: ``periods`` (movements by date range), ``by_id`` (official
    numbered statement), ``last`` / ``set_last_id`` / ``set_last_date`` (the
    server-side bookmark), ``last_statement``, ``merchant``, and
    ``import_orders`` (the multipart payment upload).

    Every documented HTTP status of §8 is mapped onto a named exception with an
    actionable message — ``409`` is the 30-second rate limit, ``500`` is a bad
    token, ``422`` is the locked history, ``413`` is the 50 000-movement cap.

    **The token is masked in everything this module raises or logs.** Fio
    carries the credential in the URL path, so an unmasked ``requests``
    exception publishes it into the server log and the record's chatter.

``utils.statement``
    ``parse_fio_xml`` and ``parse_fio_json``, sharing one ``column_NN`` map.
    XML is the primary format: its schema is published and its dates are
    unambiguous, whereas the documentation's own JSON example returns epoch
    milliseconds where its field table promises a date string.

``utils.orders``
    ``build_fio_import_xml`` renders the ``importIB.xsd`` payload from
    :class:`FioOrder` tuples, which ``order_from_item`` derives from the
    ``BankPaymentItem`` of ``account_cz_bankfile_base``. Domestic, Europlatba
    and foreign orders are emitted in the sequence §6.3 demands, and
    ``validate_order`` returns *every* problem of an order rather than raising
    on the first.

``utils.response``
    ``parse_import_response``. Note ``errorCode = 2``: the orders **were
    accepted**, with warnings.

``utils.payment_reason``
    The ČNB platební titul code list (§6.3.4), mandatory on foreign payments.

``tests.fio_fixtures``
    Sample-payload builders — movement lists in both formats and import
    responses — so every downstream module asserts against identical bytes.

Known limitations
=================

* Fio operates **no test environment** (§5.2). Everything here is tested
  against recorded fixtures with the transport stubbed; the live behaviour of a
  multi-currency account and the exact wording of the bank's per-order messages
  can only be confirmed against a real account.
* The import response's element names are documented but the shape of the tree
  around the per-order messages is not, so ``parse_import_response`` looks up
  the summary elements anywhere in the document.

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
