=========
Changelog
=========

All notable changes to **account_payment_fio** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

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

- **Czech and Slovak translations** (19 terms). The module had no ``i18n/``
  directory at all.

  These are English-source UI strings with no statutory wording, so per the
  repository convention they get English source plus ``cs.po`` / ``sk.po``
  rather than national-language source. Terms quoting Fio's own interface are
  left verbatim in **both** languages — the API rights ``Sledování účtu`` and
  ``Sledování účtu a zadávání platebních a inkasních příkazů``, the menu path
  ``Nastavení → API``, ``ID pohybu`` / ``ID pokynu`` — because Fio's API
  documentation and its internet banking are in Czech for Slovak accounts too,
  and translating them would name something the user cannot find on screen.

  *Send to Fio* is **Odeslat do Fio** / **Odoslať do Fio**, and the pair that
  resolves a lost answer reads **V bance JE** / **V bance NENÍ** (SK: **V banke
  JE** / **V banke NIE JE**) — the capitals carry the distinction, because
  getting that pair the wrong way round pays every supplier twice.

  Exported with ``tools/i18n_export_offline.py``: ``odoo-bin i18n export``
  needs a database and there is none here. Verified by reading each catalogue
  back through Odoo's own ``PoFileReader`` — every entry resolves to a record
  reference, none is untranslated — and with ``msgfmt --check``.

[19.0.1.1.1] — 2026-08-31
-------------------------

Changed
~~~~~~~

- The **Send to Fio** button carries a lightning-bolt icon (``fa-bolt``),
  matching the hand-written server action it replaces on existing installs —
  that icon is what users there recognise the action by. Kept as an ``icon``
  attribute rather than a character in the label, so it stays out of the
  translation catalogues.

[19.0.1.1.0] — 2026-08-24
-------------------------

Fixed
~~~~~

- The pre-flight check now passes the ordering account's country to
  ``validate_order``, so a Europlatba over 50 000 EUR from an account held at
  Fio's Slovak branch is reported as needing a platební titul (§6.3.2) instead
  of being refused by the bank after upload.


[19.0.1.0.0] — 2026-08-19
-------------------------

Added
~~~~~

- Payment method ``fio_xml`` on the OCA ``account.payment.order``: builds the
  ``importIB.xsd`` file with KS/VS/SS as real elements.
- Validation at confirmation time, listing every problem of the order at once.
- *Send to Fio* on a generated order, moving it to ``uploaded`` on acceptance.
  The file's format is sniffed, so ABO and pain.001 orders can be sent too.
- ``fio_payment_reason`` on the payment line, defaulting from the partner.
