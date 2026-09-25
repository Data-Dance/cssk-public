=========
Changelog
=========

All notable changes to **l10n_sk_zavierka** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

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
