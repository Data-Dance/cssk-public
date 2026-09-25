=========
Changelog
=========

All notable changes to **account_fio_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **DISCHARGED 2026-09-01 — do not port this again.** The note below was
  accurate when written and is not any more. ``18.0-fio-api`` carries the whole
  of 19.0.1.1.0 and then went further; the debt reversed direction, and this
  release is the 18.0 -> 19.0 port that settles it.

  Original note, kept for the record: everything under 19.0.1.1.0 plus the
  unreleased entries landed on ``19.0-fio-api`` only; DURWEN runs the 18.0
  copies vendored into ``DURWEN_CZ/addons``, which already carried the
  19.0.1.1.0 fixes while the ``18.0-fio-api`` branch did not.

[19.0.1.2.0] — 2026-09-01
-------------------------

Added
~~~~~

- **Czech and Slovak translations** (2 terms). The module had no ``i18n/``
  directory at all.

  These are English-source UI strings with no statutory wording, so per the
  repository convention they get English source plus ``cs.po`` / ``sk.po``
  rather than national-language source. Terms quoting Fio's own interface are
  left verbatim in **both** languages — the API rights ``Sledování účtu`` and
  ``Sledování účtu a zadávání platebních a inkasních příkazů``, the menu path
  ``Nastavení → API``, ``ID pohybu`` / ``ID pokynu`` — because Fio's API
  documentation and its internet banking are in Czech for Slovak accounts too,
  and translating them would name something the user cannot find on screen.

  Exported with ``tools/i18n_export_offline.py``: ``odoo-bin i18n export``
  needs a database and there is none here. Verified by reading each catalogue
  back through Odoo's own ``PoFileReader`` — every entry resolves to a record
  reference, none is untranslated — and with ``msgfmt --check``.

[19.0.1.1.0] — 2026-08-24
-------------------------

Fixed
~~~~~

- **The pure-function tests never ran under** ``odoo-bin``. They subclassed
  ``unittest.TestCase``, and Odoo's ``TagsSelector`` silently skips any class
  without ``test_tags`` — so ``--test-enable`` collected none of them and said
  nothing. They now subclass ``odoo.tests.BaseCase``, which is the same plain
  TestCase (no database, no cursor — the runs report 0 queries) but carries the
  ``standard``/``at_install`` tags.

- **A Fio Slovak account could not send a payment order at all.** Fio operates
  in both countries on one API — fio.cz and fio.sk share
  ``fioapi.fio.cz/v1/rest`` and one specification — but ``_account_from``
  parsed the ordering account as Czech only, so a journal configured with its
  SK IBAN (the normal Slovak setup) failed on every export. It failed badly,
  too: the underlying ``ValueError`` is not a ``FioOrderError``, so the bridges'
  ``except FioOrderError`` did not catch it and the user got a traceback rather
  than a message. ``accountFrom`` is now extracted from a CZ or an SK IBAN, and
  an ordering account of any other country is refused as a ``FioOrderError``.

Added
~~~~~

- §6.3.2's conditional platební titul: a Europlatba over 50 000 EUR **from an
  account held at Fio's Slovak branch** requires one. This is the
  specification's only rule that depends on where the payer banks, and it was
  not implemented — the bank would have rejected such an order.
  ``validate_order`` takes an optional ``home_country``, and
  ``account_from_country`` derives it from the ordering account — from the IBAN
  when there is one, otherwise from the bank code, since ``accountFrom`` is by
  definition a Fio account and Fio has exactly two (2010 CZ, 8330 SK, both
  taken from the specification's own examples). An account that is neither
  leaves the country unknown, and the rule is then skipped rather than
  guessed at.

Changed
~~~~~~~

- ``_account_from`` returns ``(country, account)`` rather than ``account``.
  Internal, but it is imported by the tests.
- ``classify`` is unchanged. Its docstring now records *why* a Slovak IBAN is a
  Europlatba rather than a domestic order even when the payer is Slovak: there
  is no Slovak domestic order type, and the specification's Slovak-specific
  rule sits in the Europlatba table, which is the evidence that SK-held
  accounts pay through ``T2Transaction``. ``T2Transaction`` carries ks/vs/ss
  natively, so nothing is lost.


[19.0.1.0.0] — 2026-08-19
-------------------------

Added
~~~~~

- Single source of truth for the Fio banka REST API (documentation v1.9 of
  16 October 2025), shared by the statement puller and both payment-order
  bridges:

  - ``utils.client.FioClient`` — every endpoint of §5 and §6, with the
    documented HTTP failures of §8 mapped onto named exceptions, and the token
    masked in every message and log record.
  - ``utils.statement`` — Fio XML and Fio JSON movement parsers over one
    shared ``column_NN`` map.
  - ``utils.orders`` — the ``importIB.xsd`` payment file, built from the
    ``BankPaymentItem`` of ``account_cz_bankfile_base``.
  - ``utils.response`` — the import response, including the ``errorCode = 2``
    accepted-with-warnings case.
  - ``utils.payment_reason`` — the 129-entry ČNB platební titul code list.
  - ``tests.fio_fixtures`` — payload builders shared by every downstream module.

- No models; helpers are imported via ``odoo.addons.account_fio_base.utils.*``.
