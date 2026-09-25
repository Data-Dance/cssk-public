=========
Changelog
=========

All notable changes to **l10n_cz_datadance** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------
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

