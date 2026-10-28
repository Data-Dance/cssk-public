=========
Changelog
=========

All notable changes to **l10n_sk_kv_dph_pos** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-10-27
-------------------------

Added
~~~~~

- The closing entry of a Point of Sale session is reported in oddiel D.1 of
  the kontrolný výkaz DPH (eKasa turnover) instead of D.2. An invoiced POS
  order stays an invoice, and a journal's own section override still wins.
