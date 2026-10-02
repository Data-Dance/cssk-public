=========
Changelog
=========

All notable changes to **l10n_sk_ju_zavierka** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- **Renamed from ``l10n_sk_ju_zavierka``.** The technical name is now
  English, like most of the repository. No migration is shipped, because the
  module was not yet installed in production. A development database that
  had it installed keeps an orphaned ``l10n_sk_ju_zavierka`` row. Install
  ``l10n_sk_single_entry_closing`` there.

[19.0.1.0.1] — 2026-09-30
-------------------------

Fixed
~~~~~

Both found by installing the module on the accountant's demo instance and
running it over a real Slovak ledger, which is where the remaining mistakes
were always going to be.

- **The exported file was named after the wrong form.** The framework names a
  statement from its ``statement_kind``, and this version must declare one of
  the four the framework knows; it declares ``profit_loss``, so the file came
  out as "Výkaz ziskov a strát — 2026-12-31.xml" — an income statement, which
  it is not. The name reaches the register with the file, so it now says
  "Účtovná závierka v JÚ (Úč FO)".
- **The unmapped-account diagnostic cried wolf.** It is written for the súvaha,
  where every balance must reach a row. Úč FO 2-01 reports majetok and záväzky
  only: the year's result comes from the denník on the other half of the
  document, equity is not reported at all (r. 21 IS the owner's equity), and
  podsúvahové accounts are outside the závierka. Unfiltered it reported 57
  unmapped accounts on the demo instance, every one of them a class 5/6, equity
  or 9xx account the form correctly ignores. Those classes are now excluded, so
  the check keeps its teeth for what it is for.

Verified on the demo instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **r. 21 ties to the cent against an outside source.** On a real 3 500-line
  ledger, Majetok celkom 88 865.54 − Záväzky celkom 56 295.39 = 32 570.15, and
  equity 3 635.34 plus the year's result 28 934.81 = 32 570.15. Since r. 21 is a
  genuine difference of two independent sums rather than a plug, that equality is
  evidence no account carrying a balance failed to reach a row.
- The export validates against the pinned schema on real data.

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- **UZFOv14 — the účtovná závierka in jednoduché účtovníctvo**, as one version
  record holding Úč FO 1-01 (12 rows, from the peňažný denník) and Úč FO 2-01
  (21 rows, from the ledger), with the official ``form.300.sk.xsd`` vendored and
  digest-pinned, and an XSD-validated export.
- A new line kind ``cash_categories`` on ``cssk.fs.statement.line.def``: its
  formula names denník category codes. § 4 ods. 6 of the opatrenie prescribes the
  denník's prehľady in the very words of the form's rows, so rows 01–03 and 05–10
  map one to one and the cash basis is read where it already lives.
- ``cssk_first_zavierka`` on the statement, which empties the preceding-period
  columns of Úč FO 2-01 (§ 22 ods. 4, vysvetlivky pt. 16). Guessed from whether
  the books reach back before the period and editable, because the PÚ case cannot
  be derived.

Fixed
~~~~~

- **A nested aggregate over a cash row read a stale zero.** The pass that
  recomputes aggregates once the denník rows hold their values iterated
  ``line_def_ids`` (sequence order), so an aggregate over an aggregate could be
  computed from the zero the framework's own pass had left and never revisited:
  no error, just a wrong total. It now walks the framework's dependency order.
  The shipped rows are sequenced safely, so this would have waited for whoever
  added the next row. Found by a second opinion from **gpt-5.3-codex**, and
  pinned by a test whose aggregates point forward — verified to fail (0.00
  against 640.00) on the old code.

Notes
~~~~~

- **Odpisy belong on Úč FO 1-01**, in r. 10 Ostatné výdavky (§ 4 ods. 9). The
  first draft excluded the denník's non-cash rows from the statement on the
  reasoning that a statement of money cannot hold an odpis. The opatrenie says
  otherwise, and the opatrenie wins.
- **The schema is not where the others are.** Every other statutory schema in
  this repository comes from ``ekr.financnasprava.sk/Formulare/XSD/``; 22
  plausible names were probed there and all 404'd, while a control fetch on the
  same path succeeded. This one is served beside the eForm and named by it.
- **The schema caught a real mistake on the first run**: ``nazovUJ`` takes two
  repeated ``riadok`` elements, not ``riadok1``/``riadok2``.
- **Row tokens are 3-digit synthetics.** A six-digit token matches only codes
  starting with it, so ``221000`` reported zero on a chart whose bank account is
  ``221100``.
- **The partition test found real holes on its first run.** Poskytnuté preddavky
  na dlhodobý majetok (051/052/055 with their 095 opravné položky), komplexné
  náklady budúcich období (382), derivatives (373/376) and the long-term
  liabilities 471/473/478/481 reached no row at all, so their balances would have
  vanished from the statement in silence. Equity reaches no row by design: r. 21
  "Rozdiel majetku a záväzkov" IS the owner's equity, computed from two
  independent totals rather than plugged, so the statement stays able to fail.
- **Development note:** the version record is ``noupdate="1"``, which is right in
  production — an upgrade must not overwrite an accountant's edits — but it means
  a changed row formula does NOT reach an existing database on ``-u``. Drop the
  record and upgrade again, or the tests read the old rows and pass or fail for
  the wrong reason. This cost two puzzled runs.
- Long-term deposits and receivables stay in r. 11 and r. 08 rather than r. 03:
  maturity is not in the account code, and a manual override records who moved
  them.
