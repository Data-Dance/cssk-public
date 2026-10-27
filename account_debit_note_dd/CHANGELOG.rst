=========
Changelog
=========

All notable changes to **account_debit_note_dd** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Posting is Odoo's again.** The module replaced Odoo's posting routine with
  an old copy for every journal entry, invoice and bill in the database. That
  copy skipped five checks — a negative invoice total, an untrusted company bank
  account, an account that does not fit the journal, an account of another
  company, an archived analytic account — and cut off the posting additions of
  other installed modules. Those checks apply again, and the other modules'
  additions run. A debit note with a negative total can no longer be posted:
  issue a credit note for a reduction.
- **The customer Credit Notes list showed vendor debit notes.** It now shows
  customer credit notes and customer debit notes only.
- **A debit note printed in Slovak was titled in English.** Slovak titles are
  *Ťarchopis*, *Návrh ťarchopisu* and *Zrušený ťarchopis*.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Extends OCA ``account_debit_note`` with Data Dance customisations to ``account.move``
  posting/handling for debit notes (vrubopis).
- Dedicated debit-note invoice report template (``report/report_invoice.xml``) and
  form-view adjustments (``views/account_move_views.xml``).
