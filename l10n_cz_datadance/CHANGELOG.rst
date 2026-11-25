=========
Changelog
=========

All notable changes to **l10n_cz_datadance** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **The cross-checks of 19.0.1.3.0 are not on 18.0.** Port the engine, the
  three actions, the buttons and the tests together.

[19.0.1.4.0] — 2026-11-24
-------------------------

Added
~~~~~

- **Five more switches** in the settings, for Czech modules that existed but
  could only be installed from the Apps list: *Účetní vzory*
  (``l10n_cz_account_move_template``), *Účetní závěrka*
  (``l10n_cz_fiscal_year_closing``), *Protokoly k majetku*
  (``l10n_cz_asset_protocol_oca``), *Manažerské výkazy*
  (``l10n_cz_mis_reports``) and *Vytěžování faktur (AI)*
  (``account_invoice_ai_extract``, delivered to subscribers).

[19.0.1.3.0] — 2026-11-24
-------------------------

Added
~~~~~

- **Cross-checks before filing**, as the Slovak suite has them, with the
  Czech links taken from the forms themselves. *Porovnat s přiznáním* on a
  kontrolní hlášení compares its eight control rows (věta C) with ř. 1, 2,
  40, 41, 25, 10, 11 and 3 + 4 + 5 + 6 + 9 + 12 + 13 of the přiznání, within
  the 1 000 Kč the structure allows; on a souhrnné hlášení it compares codes
  0 + 1, 3 and 2 with ř. 20, 21 and 31. *Porovnat s účetnictvím* on a
  přiznání compares ř. 62 and ř. 46 with the tax lines booked on account 343
  and shows what moved on 343 with no tax behind it.
- For a quarterly přiznání the three monthly hlášení are added; if one is
  not computed the rows are informational, not differences.

[19.0.1.2.0] — 2026-11-15
-------------------------

Added
~~~~~

- The bundle now installs ``l10n_cz_inventory_verification``: inventurní
  soupisy and the record of the inventarizace (§ 29–30 zákona č. 563/1991
  Sb.), as the Slovak bundle installs its counterpart. An existing database
  gets the module on upgrade.

[19.0.1.1.2] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech catalogues: translated the strings that were still English.

[19.0.1.1.0] — 2026-08-27
-------------------------

Changed
~~~~~~~

- Relicensed from ``Other proprietary`` to **AGPL-3**.
- ``l10n_cz_fs`` (Rozvaha + VZZ) and ``l10n_cz_dppo`` moved out of ``depends``
  and onto ``Settings → Accounting`` toggles, for the same reason as the Slovak
  bundle: both are delivered to subscribers rather than published.


[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- One-click Czech statutory localization meta-installer: pulls in the statutory core in a single
  step — Kontrolní hlášení (DPHKH1), souhrnné hlášení (DPHSHV), přiznání k DPH (DPHDP3),
  Rozvaha + Výsledovka, DPPDP9, CZ invoice, VIES, saldokonto/zápočet (partner balances) and
  dohadné (accruals).
- Optional workflow pieces (dual depreciation, Method A, advance invoices) selectable in
  Settings → Accounting → Czech localization.

[19.0.1.1.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Czech screen. The template and the catalogues now carry them,
  and the Czech is written.

