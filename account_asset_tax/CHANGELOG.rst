=========
Changelog
=========

All notable changes to **account_asset_tax** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.9.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.9.3] — 2026-07-04
-------------------------

Added
~~~~~

- Combined **book-vs-tax depreciation** report (``account.asset.book.tax.report``):
  one row per (asset, fiscal year) comparing ``book_amount`` (all book
  depreciation) vs ``book_amount_posted`` (posted subset — the statutory figure)
  vs ``tax_amount``, with ``difference = book − tax`` as the DPPO add-back
  (pripočítateľná / § 23 ods. 3) or deduction. Implemented here as an abstract
  SQL-view mixin (``account.asset.book.tax.report.mixin``, tax-side CTE + FULL
  OUTER JOIN); each bridge supplies the concrete model and the book side. Exposed
  as pivot / graph / list under *Accounting → Reporting → Book vs Tax
  Depreciation*, with a company ``ir.rule`` and read ACL.

[19.0.1.7.0]
------------

Added
~~~~~

- Deferred-tax posting: optional *Post immediately* (else draft).
- DPPO Table B PDF report (QWeb) alongside the XLSX export.
- Interactive cheat-sheet: CZ §31 increased-first-year selector (verified vs Python engine).
- Comprehensive cs/sk translations (122/190 strings).
- Cheat-sheet note on component depreciation (accounting method; tax keeps the asset whole).

Verified
~~~~~~~~

- Full re-validation on 19CE-TEST + 19EE-TEST; engine 20 tests, OCA 12, EE 14 — all green.

[19.0.1.6.0]
------------

Added
~~~~~

- Close-fiscal-year wizard: freeze (file) the board up to a year across all assets + lock method.
- Vehicle base cap (CZ §30e 2M CZK / SK §17(34) 48k EUR): company cap amount + per-asset flag + engine cap. (SK is a documented conservative base-cap of the add-back rule.)
- Deferred-tax POSTING: company 481/592 + journal config; reconciliation button creates a reviewable DRAFT JE truing the 481 balance to the closing position.
- DPPO Table B XLSX export from the reconciliation (xlsxwriter, no extra module dep).
- Tax-default fields plumbing (read by bridges from asset model / profile).
- Module icon; cs/sk translations (i18n/cs.po, sk.po — key UI strings).

Verified
~~~~~~~~

- Full validation on 19CE-TEST + 19EE-TEST after each feature; translations load.

[19.0.1.5.0]
------------

Added
~~~~~

- Disposal hook helper ``_tax_register_disposal`` (idempotent) + ``tax_residual_on_disposal()``.
- Deferred tax in the DPPO reconciliation: ``tax_rate`` input (default 21 %), per-asset accounting NBV vs tax residual → temporary difference → deferred tax (DTL/DTA), with totals. New abstract reader ``_tax_accounting_residual(date)``.
- CZ §31 increased-first-year rates (+10/15/20 %, groups 1–3, first depreciator): engine ``CZ_INCREASED_FIRST_YEAR`` tables (verified vs zákon 586/1992 Sb.), ``tax_increased_first_year`` selection on the asset, constraint (CZ + linear + groups 1–3). Engine tests added (17 total).

[19.0.1.4.2]
------------

Fixed
~~~~~

- Double-count bug (found via EE integration test on 19EE-TEST): a technical-improvement event both raised ``tax_entry_value`` AND was replayed by the board recompute, so an improved asset over-depreciated by the improvement amount. ``_add_tax_event`` no longer touches ``tax_entry_value`` — the event is the single source of truth; the increase shows in the board/residual.

[19.0.1.4.1]
------------

Fixed
~~~~~

- Load fixes found installing on a real DB (19CE-TEST, CE):

  - abstract mixin Monetary fields failed standalone setup → added own ``tax_currency_id`` (compute, no depends); moved the ``tax_line_ids``-dependent ``tax_value_residual``/``tax_value_depreciated`` computes to the bridges; dropped ``@api.depends`` referencing non-owned fields.
  - search view: removed the ``<group expand=…>`` "Group By" wrapper (invalid in Odoo 19) → top-level group-by filter.

Verified
~~~~~~~~

- Installs clean on Odoo 19 CE (19CE-TEST); registry loads, 0 errors.

[19.0.1.4.0]
------------

Added
~~~~~

- Statutory method/group lock enforced server-side: ``write()`` blocks changing ``tax_method`` / ``tax_class_id`` while ``tax_method_locked`` (CZ §30(2) / SK §26(3)).
- Guard: a technical-improvement event on a §30a (extraordinary) asset is refused — under §30a(3) it is a separate asset (engine raises; ``_add_tax_event`` raises a clear UserError). Engine test added (15 total, green).

[19.0.1.3.0]
------------

Added
~~~~~

- Interactive accounting cheat-sheet (``static/description/cheat_sheet.html``): a self-contained HTML/JS app (matching the Method A / Advance Invoice ones) that builds the depreciation board year-by-year with a Play/Next/Reset stepper, CZ/SK + group + method + in-service-month + entry-value controls, a lifecycle-event toggle (improvement/suspension/disposal), and a live accounting-vs-tax DPPO 150/250 tally. Its tax math is a JS port of the Python engine, verified to match all 14 golden values (incl. events) via node.

Changed
~~~~~~~

- Store-page ``index.html`` links both cheat sheets and uses the correct ``account_asset_tax_oca`` bridge name.

[19.0.1.2.0]
------------

Added
~~~~~

- Backfill wizard (``account.asset.tax.backfill``) for migrating mid-life assets: lays out the full statutory board, freezes years up to the filed fiscal year, leaves the open tail. Optional expected-residual cross-check refuses to backfill on a statutory mismatch (points to an unmodelled past event or wrong in-service date).
- ``tax_in_service_date_override`` on the asset (tax in-service date may differ from the accounting start); used by the engine spec and surfaced on the form.
- *Backfill (migration)* button on both bridge asset forms.

[19.0.1.1.0]
------------

Added
~~~~~

- Lifecycle events (``account.asset.tax.event``): technical improvement (CZ increased-price rate / increased-residual coefficient; SK increased price / residual), suspension (CZ calendar-shift / SK life-extension), disposal (CZ half-year §26(7) / SK monthly pro-rata). Events are persisted and replayed so recompute is idempotent.
- Engine functions ``apply_technical_improvement``, ``apply_suspension``, ``apply_disposal`` with 5 added golden tests (13 total, all green).
- DPPO reconciliation wizard (``account.asset.tax.reconciliation``): per-asset accounting-vs-tax comparison for a period → add-back (line 150) / deduction (line 250), under Accounting ▸ Reporting.
- Event wizard launched from the asset form.

Renamed
~~~~~~~

- OCA bridge ``account_asset_tax_cssk_oca`` → ``account_asset_tax_oca``.

[19.0.1.0.0]
------------

Added
~~~~~

- Country-neutral core for CZ/SK dual depreciation.
- ``account.asset.tax.class`` — statutory depreciation group (life, rates, coefficients, allowed methods).
- ``account.asset.tax.line`` — non-posted tax-depreciation board line (asset relation added by the bridge).
- ``account.asset.tax.mixin`` — tax fields + engine orchestration mixed into ``account.asset`` by a bridge.
- ``engine.depreciation`` — pure-Python calculator for CZ §31/§32/§30a and SK §27/§28, verified against the 2026 consolidated statutes; 8 golden tests in ``tests/test_engine.py``.
- Compute wizard, tax-group configuration views and menu.
- Accounting cheat sheet (``docs/``, rendered to ``static/description/``).
