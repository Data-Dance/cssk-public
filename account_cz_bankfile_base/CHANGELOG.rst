=========
Changelog
=========

All notable changes to **account_cz_bankfile_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.3.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Code translations Odoo was never loading: an entry
  referencing ``code:addons/...`` needs the extracted comment
  ``#. odoo-python`` or it is silently ignored. Repaired by
  ``tools/fix_po_code_comments.py``.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.3.0] — 2026-09-01
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

[19.0.1.2.0] — 2026-09-01
-------------------------

Added
~~~~~

- **``parse_national_account``** — generalises ``parse_cz_account`` to accept a
  CZ *or* SK IBAN, returning the country alongside the prefix, account and bank
  code. ``parse_cz_account`` stays as the CZ-only view, because every ABO and
  MultiCash call site means "a Czech account", and it keeps its own refusal
  message: "not a Czech account" says the useful thing where the generic
  wording does not.

  ``countries`` defaults to CZ alone so the Czech-only formats keep refusing
  everything else. CZ and SK IBANs are structurally identical, so quietly
  accepting an SK one into a Czech file format would build a plausible-looking
  file that the bank then rejects. Fio's XML, which serves both countries on one
  API, passes ``('CZ', 'SK')``.

Fixed
~~~~~

- **Unblocks ``account_payment_fio`` and ``account_payment_fio_batch`` on this
  branch.** ``account_fio_base/utils/orders.py`` imports
  ``parse_national_account`` and nothing defined it, so both payment bridges
  raised ``ImportError`` and could not install. ``account_fio_base`` itself was
  unaffected at load — both its ``__init__.py`` files are empty, so
  ``utils.orders`` is not reached — but two of its test suites errored.

  Ported from ``18.0-fio-api`` (``account_cz_bankfile_base`` 18.0.1.2.0), where
  it was written and live-tested, together with its unit tests.

[19.0.1.1.0] — 2026-08-11
-------------------------

Added
~~~~~

- ``utils.common.payments_to_items`` — maps ``account.payment`` records to
  ``BankPaymentItem``, shared by the Enterprise ``account_abo_batch`` and
  ``account_multicash_batch`` bridges so the mapping is not written twice.
  Duck-typed: reads the ``l10n_cssk_payment_symbols`` and ``account_iso20022``
  fields defensively, so the module still depends on ``base_iban`` alone.

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
