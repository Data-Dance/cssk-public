=========
Changelog
=========

All notable changes to **account_payment_fio** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.4.1] — 2026-09-01
-------------------------

Fixed
~~~~~

- **A test had been shadowing another and never ran.** Two methods in
  ``TestFioPaymentOrder`` shared the name
  ``test_a_non_numeric_symbol_is_refused_at_entry``, so Python kept the second
  and the first was dead: the **variable symbol** half of
  ``_check_payment_symbols_cz`` had never been exercised on either branch. Both
  are now named for the field they cover. The constraint itself was correct —
  ``"FA/42".isdigit()`` is false and the rule covers ``variable_symbol`` — so
  this restores coverage rather than fixing behaviour, but a test suite that
  silently drops a case is worth less than its green tick suggests.

  Found by an AST scan for duplicate method names across every suite in the Fio
  family; the rest are clean.

Carry-over to 19.0
~~~~~~~~~~~~~~~~~~

- cs/sk catalogues (18.0.1.4.0) are absent on 19.0, as they are for the whole
  Fio family.

[18.0.1.4.0] — 2026-09-01
-------------------------

Fixed
~~~~~

- **3 view terms were missing from the translation catalogues.** The offline
  exporter read only the first child of a view's ``arch``, and an inherited
  view normally has one top-level node per xpath — so every term after the
  first was silently absent. Among them were the alert telling an operator that
  the bank's answer to an upload was lost, and the 90-day history-unlock
  instruction: precisely the messages whose whole value is being read under
  time pressure. Fixed in ``tools/i18n_export_offline.py`` and re-exported.

[18.0.1.3.0] — 2026-08-31
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

[18.0.1.2.0] — 2026-08-31
-------------------------

Changed
~~~~~~~

- *Send to Fio* carries a lightning-bolt icon, so the one button that moves
  real money is not visually identical to the ones that do not. The icon is an
  ``icon="fa-bolt"`` attribute rather than a character in the label, so it
  stays out of every translation catalogue.

[18.0.1.1.0] — 2026-08-25
-------------------------

Fixed
~~~~~

- The pre-flight check now passes the ordering account's country to
  ``validate_order``, so a Europlatba over 50 000 EUR from an account held at
  Fio's Slovak branch is reported as needing a platební titul (§6.3.2) instead
  of being refused by the bank after upload.


[18.0.1.0.0] — 2026-08-19
-------------------------

Added
~~~~~

- Payment method ``fio_xml`` on the OCA ``account.payment.order``: builds the
  ``importIB.xsd`` file with KS/VS/SS as real elements.
- Validation at confirmation time, listing every problem of the order at once.
- *Send to Fio* on a generated order, moving it to ``uploaded`` on acceptance.
  The file's format is sniffed, so ABO and pain.001 orders can be sent too.
- ``fio_payment_reason`` on the payment line, defaulting from the partner.
