=========
Changelog
=========

All notable changes to **l10n_sk_inventarizacia** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_sk_inventarizacia``.** The technical name is now
  English, like most of the repository. No migration is shipped, because the
  module was not yet installed in production. A development database that
  had it installed keeps an orphaned ``l10n_sk_inventarizacia`` row. Install
  ``l10n_sk_inventory_verification`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_sk_inventarizacia``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_sk_inventarizacia``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
