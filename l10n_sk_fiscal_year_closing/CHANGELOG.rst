=========
Changelog
=========

All notable changes to **l10n_sk_zavierka** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_sk_zavierka``.** The technical name is now English,
  like most of the repository. No migration is shipped, because the module
  was not yet installed in production. A development database that had it
  installed keeps an orphaned ``l10n_sk_zavierka`` row. Install
  ``l10n_sk_fiscal_year_closing`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_sk_zavierka``. Rename it together with the rest of the 2026-09-30
  batch (the fiscal-year closing, surcharges, annual tax settlement and
  inventory verification modules). Rename every reference too: dependent
  manifests, ``odoo.addons.*`` imports, the ``.pot`` file name and
  ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_sk_zavierka``. Rename it together with the rest of the 2026-09-30
  batch (the fiscal-year closing, surcharges, annual tax settlement and
  inventory verification modules). Rename every reference too: dependent
  manifests, ``odoo.addons.*`` imports, the ``.pot`` file name and
  ``module_*`` settings toggles. The 19.0 commit is the checklist.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Slovak year-end closing template on the OCA ``account_fiscal_year_closing``
  engine: trieda 5/6 → **710**, triedy 0–4 and 710 → **702**, reopened via **701**.
- Retyping of 701/702/710 from ``off_balance`` to ``equity`` — Odoo refuses to mix
  off-balance accounts with ordinary ones, so the závierka could not be posted at
  all otherwise. Chart template for new companies, post-init hook for existing.
- ``_mapping_move_lines_get`` override mirroring every closed account onto 702
  instead of posting only the net, which on a balanced sheet is zero and would
  leave 702 out of the entry entirely.
- ``inverse_move_prepare`` override rerouting the opening counterpart from 702 to
  701; the engine's plain reversal would otherwise use 702 on both sides.
- 6 tests covering all three.

Gotcha worth carrying
~~~~~~~~~~~~~~~~~~~~~

Passing ``amount_currency=0`` on a move line that has no foreign currency makes
Odoo derive the balance *from* it and zero the line — silently unbalancing the
entry. Only set ``amount_currency`` when the source line actually has one.
