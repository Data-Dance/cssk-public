=========
Changelog
=========

All notable changes to **l10n_sk_inventarizacia** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_sk_inventarizacia``**, as on 19.0 (2026-09-30). The
  technical name is now English, like most of the repository. No migration
  is shipped, because the module was not yet installed in production. A
  development database that had it installed keeps an orphaned
  ``l10n_sk_inventarizacia`` row. Install ``l10n_sk_inventory_verification``
  there.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- ``l10n.sk.inventarizacia`` with the three § 30 ods. 2 dates, the § 30 ods. 3
  zápis fields (porovnanie, posúdenie reálnosti ocenenia, signature) and totals.
- ``l10n.sk.inventurny.supis`` — fyzická or dokladová, with miesto uloženia,
  hmotne zodpovedná osoba and the person who established the actual state.
- ``l10n.sk.inventurny.supis.line`` carrying množstvo, jednotka and cena
  separately, per § 30 ods. 2 písm. e).
- Dokladová inventúra reads the account's ledger balance as at the deň ku
  ktorému (posted entries only), so the comparison is computed.
- Closing is refused without a súpis, and without the § 30 ods. 2 písm. i)
  signature on each súpis.
- QWeb reports for both the inventúrny súpis and the inventarizačný zápis.
- 8 tests.
