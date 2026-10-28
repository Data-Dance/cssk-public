=========
Changelog
=========

All notable changes to **l10n_cz_fs** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.2.0] — 2026-10-27
-------------------------

Added
~~~~~

- **The Rozvaha and the Výkaz zisku a ztráty in plný rozsah.** Two new
  versions carry every item of přílohy 1 and 2 of vyhláška č. 500/2002 Sb.,
  in the statute's order: B.I.2.1. Software, C.II.2.4.3. Stát – daňové
  pohledávky, D.2.1–D.2.2, E.1–E.3, IV.1–IV.2, V., VI.1–VI.2, J.1–J.2 and the
  rest. A commercial company files the výkaz zisku a ztráty in full
  (§ 3a odst. 3 písm. a) and can now do so from Odoo.
- **Account tags for the items no account number can tell apart:** IV. / V.
  (both on 665), the ovládaná osoba items IV.1, V.1, VI.1 and J.1, and E.1.2 /
  E.2 of 559. Untagged amounts go to the "ostatní" item, so nothing needs
  setting up where there are no such flows. An account carries at most one.
- In the full-scope rozvaha, 221, 336, 341–347, 373 and 481 are reported on
  the side their own balance dictates (an overdraft as a bank liability, a
  tax prepayment as a receivable, a deferred tax asset as C.II.1.4), and 491
  is A.I.1 as § 14 of the decree says.
- The XML export states the rozsah in its header.

Changed
~~~~~~~

- **New Rozvaha and Výkaz zisku a ztráty statements default to the plný
  rozsah.** The existing versions are renamed "(zkrácený rozsah)" on upgrade
  (unless you renamed them) and remain available in the Version field;
  statements already computed on them are unchanged.

[19.0.1.1.2] — 2026-10-27
-------------------------

Changed
~~~~~~~

- **The module no longer claims the full statutory structure.** The Rozvaha
  carries the items of the zkrácený rozsah and the Výkaz zisku a ztráty lacks
  V., D.2.1–D.2.2, E.1–E.3, IV.1–IV.2, V.1–V.2, VI.1–VI.2 and J.1–J.2, which an
  obchodní společnost must file (vyhláška č. 500/2002 Sb., § 3a odst. 4). The
  description and README now say so, as the user guide already did.

[19.0.1.1.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Rozvaha A.V. is the result of the period, not since the first entry.**
  A.V. Výsledek hospodaření běžného účetního období read the cumulative
  balance of classes 5 and 6, so on a database holding more than one year
  without a closing it reported every earlier year's result as this year's.
  It now reads the movement within the period and equals the result of the
  výkaz zisku a ztráty. Earlier results belong in A.IV. through 428/429/431;
  where a year was never closed, AKTIVA and PASIVA now differ by that year's
  result instead of hiding it in A.V. On an existing database the shipped row
  is updated on upgrade unless it was edited.

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
