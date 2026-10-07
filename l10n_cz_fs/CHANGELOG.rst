=========
Changelog
=========

All notable changes to **l10n_cz_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-28
-------------------------

Changed
~~~~~~~

- **Rozvaha aktiva in brutto / korekce / netto.** B.I., B.II., B.III., C.I.,
  C.II. and C.III. now name their oprávky and opravné položky (07x, 08x, 09x,
  19x, 291, 391) in the correction formula instead of netting them into the
  row. Netto is unchanged. The DPPDP9 return files the Rozvaha as VetaUA with
  ``kc_brutto`` / ``kc_korekce`` / ``kc_netto`` per row, and a netted figure
  cannot be split back into those columns. Migration included: the version
  lives in a ``noupdate="1"`` file, and each row is rewritten only where it
  still holds the formula this module shipped.

Fixed
~~~~~

- **094 (opravná položka k nedokončenému DHM) sat in B.I.** It belongs to
  B.II. Dlouhodobý hmotný majetek; B.I. and B.II. were each misstated by its
  balance, while B. Stálá aktiva was right.

[19.0.1.0.2] — 2026-09-06
-------------------------

Fixed
~~~~~

- Every Rozvaha / VZZ / Přehled export raised: no XSD is published for any of
  them (they are filed inside the DPPO envelope), and the core mixin had been
  tightened to refuse what it could not validate. The four versions now declare
  ``xml_schema_optional``, with a migration because they live in a
  ``noupdate="1"`` file — an upgrade would otherwise take the fix and leave the
  database broken, showing up only when somebody tries to file.
- Test fixture sets a finanční úřad. ``l10n_cz_statutory`` adds a preflight
  requiring the c_ufo and this module does not depend on it, so the suite was
  green standalone and red on every full-bundle install.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
