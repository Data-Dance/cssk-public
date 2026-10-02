===============================================
KB BEST Format — shared builders and parser
===============================================

The single source of truth for **BEST**, Komerční banka's fixed-width client
format for its direct-banking channels (MojeBanka Business, Profibanka, Přímý
kanál). One format covers both directions:

* ``build_best_domestic`` — domestic payment batch: úhrady and inkasa
  (record ``01``, 353 bytes);
* ``build_best_foreign`` — foreign and SEPA payment batch (record ``02``,
  884 bytes, followed by the ``03`` structured address);
* ``parse_best_statement`` — electronic statement ``*.OKM`` / ``*.KMO``
  (``51`` turnover, ``52`` transactions, 475 bytes) into the OCA
  statement-import triplets; ``is_best_statement`` sniffs it.

There are **no Odoo models** — pure helpers imported via
``odoo.addons.account_kb_best_base.utils.best``. The shims are
``account_payment_kb_best`` and ``account_statement_import_kb_best``.

BEST is Komerční banka's, not ČSOB's
====================================

The work item this came from asked for "ČSOB BEST". No ČSOB publication of
a BEST format could be found: the CEB format documents ČSOB publishes cover
payment batches in ABO, MultiCash, XML and XLS/XLSX and statements in GPC, TXT
and XML (as of 2026-09-28). BEST is KB's — the name is KB's own ("Standardní
formát dat, podporovaný aplikacemi přímého bankovnictví KB") — and KB publishes
it in full, so that is what is implemented here.

What the builders enforce
=========================

Each rule is the specification's, not a guess:

* The debited account must be a KB account (bank code ``0100``).
* ``Sekv_No`` must be unique for the client **per creation day across every
  file** — it is taken from the payment line's database id (base 36), because a
  per-file counter would collide with the morning's batch.
* Due date not before today; amounts ``9(13)V9(2)``; the trailer carries the
  count and the sum of the amounts.
* Domestic: a payment in another currency than the account's goes with the
  counter-currency and conversion flag ``P``; a non-CZK counter-currency only
  to another KB account; a direct debit outside KB only in CZK; the constant
  symbols KB refuses in a batch (``???5``, ``??51``, ``0006``, ``0007``) are
  refused before the bank does.
* Foreign: SWIFT character set only, no field starting with ``-`` or ``:``;
  **SEPA** (flag ``Y``, charges ``SLV``) when EUR, an IBAN in a SEPA country and
  shared charges; into the EEA only with ``SHA`` (PSD2, since 13 Jan 2018); EUR
  into the EEA needs an IBAN; a non-SEPA payment needs the beneficiary's name,
  street, city and country and a BIC or the bank's name, city and country.
  ``/VS/`` and ``/KS/`` are written into the remittance, where KB reads them
  back into the transaction history.

Statement parsing
=================

Signs come from the accounting code — ``0`` debit, ``1`` credit, ``2`` debit
reversal, ``3`` credit reversal — which is the spec's own check
``NZ = SZ − OD + OK``. ``53`` records (non-accounting loan interest and fee
instalments) do not move the balance and are skipped. SS ``9999999999`` is an
instruction to suppress the partner's name, not a symbol, and is dropped.

Specification
=============

Komerční banka — *Klientský formát BEST podporovaný v KB* (valid from
20 June 2026), fetched 2026-09-28:

* https://mojebanka.kb.cz/file/cs/format_best.pdf (English edition:
  https://mojebanka.kb.cz/file/en/format_best_en.pdf)
* KB's sample files, against which every field offset was checked:
  https://www.mojebanka.cz/file/cs/Priklad_DPL_BEST.ikm (domestic),
  https://www.mojebanka.cz/file/cs/Priklad_ZPL_BEST.ikm (foreign/SEPA),
  https://www.mojebanka.cz/file/cs/Priklad_20170510_CZK.okm and
  https://www.mojebanka.cz/file/cs/Priklad_20170510_USD.okm (statements —
  both parse and reconcile to the turnover record's closing balance).

Credits
=======

Author: Data Dance s.r.o. — https://www.datadance.eu
