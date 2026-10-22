=========
Changelog
=========

All notable changes to **account_cz_bankfile_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- **``national_account_key``** (with its ``_AccNumber`` shim), ported from 19.0.
  Returns ``(bank, prefix, number)`` for a CZ/SK account in either spelling, so
  a statement import can find the journal a file belongs to without comparing
  strings that never match. ``account_statement_import_kb_best`` and
  ``account_statement_import_mt940`` import it at module level, so without it
  neither loads — which is how it was found: the registry failed to load.

  Verified against 19.0's implementation on six inputs, including both IBAN and
  ``prefix-account/bank`` spellings of the same account and the None cases.

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- **``parse_national_account`` (18.0.1.2.0) is needed on 19.0 and is not
  there.** ``19.0-fio-api``'s ``account_fio_base/utils/orders.py:32-36``
  imports the name and nothing on that branch defines it. The blast radius is
  narrower than it first looks, because ``account_fio_base``'s ``__init__.py``
  and ``utils/__init__.py`` are both empty, so ``utils.orders`` is not reached
  at module load: ``account_fio_base`` itself installs (two of its test files
  error), and ``account_fio`` / ``account_statement_fio`` are untouched. What
  cannot install is **``account_payment_fio``** (``models/
  account_payment_order.py:15``) and **``account_payment_fio_batch``**
  (``models/account_batch_payment.py:16``), which import it directly.

  Nothing released is affected — the whole Fio family is absent from the
  ``19.0`` branch — but it blocks whoever next installs the payment bridges
  from that feature branch.

[18.0.1.3.0] — 2026-08-31
-------------------------

Added
~~~~~

- **Czech and Slovak translations** (16 terms). The module had no ``i18n/``
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

Fixed
~~~~~

- **The pure-function tests never ran under** ``odoo-bin``. They subclassed
  ``unittest.TestCase``, and Odoo's ``TagsSelector`` silently skips any class
  without ``test_tags`` — so ``--test-enable`` collected none of them and said
  nothing. They now subclass ``odoo.tests.BaseCase``, which is the same plain
  TestCase (no database, no cursor — the runs report 0 queries) but carries the
  ``standard``/``at_install`` tags.

[18.0.1.2.0] — 2026-08-25
-------------------------

Added
~~~~~

- ``parse_national_account(partner_bank, countries=('CZ',))``, returning
  ``(country, prefix, account, bank_code)``. CZ and SK IBANs are structurally
  identical, so a caller that can send to both — Fio, whose XML serves one API
  for two countries — can now say so, while ABO and MultiCash keep refusing
  everything that is not Czech. The country of the national
  ``[prefix-]account/bank`` form is reported as ``None``: it names no country,
  and the 4-digit bank code cannot be used to guess one.
- A test module. The parser four bank-file formats depend on had none, and the
  new cases pin ``parse_cz_account``'s refusal of SK IBANs as deliberate.

Changed
~~~~~~~

- ``parse_cz_account`` now delegates to ``parse_national_account``. Its
  signature, its return value **and its refusal message** are unchanged on
  every input — ABO and MultiCash surface that message to the user, so it is
  restated in the wrapper rather than inherited from the generic one. Verified
  differentially against the previous implementation over the account forms,
  ``acc_type`` values and malformed inputs.


[18.0.1.1.0] — 2026-08-19
-------------------------

Added
~~~~~

- ``utils.common.payments_to_items`` — the ``account.payment`` →
  ``BankPaymentItem`` mapping, back-ported from 19.0 so the Enterprise bridges
  (``account_payment_fio_batch``, and ``account_abo_batch`` /
  ``account_multicash_batch`` when they follow) share one mapping with the
  Community side instead of each writing their own.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Single source of truth for the Czech/Slovak bank payment-file formats, exposed as
  pure helpers under ``odoo.addons.account_cz_bankfile_base.utils.*`` (no models):

  - ``utils.abo.build_abo_file`` — ABO credit-transfer (úhrada) file
  - ``utils.multicash.build_multicash_file`` — MultiCash CFD/CFU/CFA/MT101
  - ``utils.common`` — Czech account parsing, the normalized ``BankPaymentItem``
    input record, and the VS/KS/SS symbol resolver.

- Builders take a list of ``BankPaymentItem`` (plain values + bank records), so the
  CE (``account_payment_order`` → ``account.payment.line``) and EE
  (``account_batch_payment`` → ``account.payment``) shims feed them without
  duplicating any format logic.
