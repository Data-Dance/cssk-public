=========
Changelog
=========

All notable changes to **l10n_cz_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Evaluator rewritten to use ``_read_group`` balance helpers instead of per-prefix search loops —
  the Rozvaha compute drops from ~600 queries to 2. (Wave 3)

[2026-07-01] — Wave 1 (correctness)
-----------------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``).
- Multi-company ``ir.rule`` (``company_id in company_ids``) added so statements no longer leak
  across companies.

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech financial statements on ``l10n_cssk_fs_base``, CE-clean — line values summed from
  ``account.move.line`` by account-code prefix (balance sheet cumulative as-of date, P&L period
  movement).
- Rozvaha (plný rozsah) + Výkaz zisku a ztráty v druhovém členění per vyhláška 500/2002 Sb.;
  every l10n_cz account maps to exactly one leaf line, so AKTIVA = PASIVA and výsledek
  hospodaření = výnosy − náklady reconcile (partition verified in tests).
- Přehled o peněžních tocích (cash flow, nepřímá metoda) and Přehled o změnách vlastního
  kapitálu (changes in equity) as příloha components, reconciling by construction
  (A + B + C = Δcash; počátek + Σ změny = konec).
- Structured XML export as a stand-in (the full závěrka has no standalone EPO XSD).
- cs_CZ jsonb translations (i18n sweep).
