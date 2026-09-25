=========
Changelog
=========

All notable changes to **l10n_sk_currency_revaluation** are documented here.
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

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: thin chart-preset bridge pre-filling the OCA multicurrency-revaluation accounts with the Slovak **563** / **663** (kurzové rozdiely) accounts. AGPL-3 (depends on the AGPL OCA engine); mapping applied via post-init hook.
