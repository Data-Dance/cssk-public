=========
Changelog
=========

All notable changes to **l10n_cz_currency_revaluation** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- revaluation journal = the chart's exch journal (template + hook) — 19.0.1.4.0.
- Accountant role implies group_revaluation_additional (data/security.xml);
  KURZ named in cs/sk/en — 19.0.1.3.0. Check 18.0 has the same OCA group
  first.

[19.0.1.4.0] — 2026-11-04
-------------------------

Changed
~~~~~~~

- **Revaluation goes through the company's exchange-difference journal.** A
  Czech chart now sets ``currency_reval_journal_id`` to the chart's ``exch`` journal, and
  the install hook uses an existing KURZ or that journal before it creates a
  new KURZ. Before, a chart loaded with English active (code EXCH) ended up
  with two exchange journals: Odoo's and our KURZ. Existing companies keep
  the journal they have.

[19.0.1.3.0] — 2026-11-04
-------------------------

Fixed
~~~~~

- **Nobody saw the revaluation menus.** account_multicurrency_revaluation
  shows *Currency Revaluation* and *Reverse Currency Revaluation* only to its
  group *Additional provisioning entries posting*, which no role implied. The
  *Accountant* role (*Hlavní účetní*) now implies it, for existing members
  too.
- **The KURZ journal had only its Czech name**, stored as the English one;
  it is now *Kurzové rozdíly* / *Kurzové rozdiely* / *Exchange Rate
  Differences*. The upgrade renames it unless you renamed it. Where KURZ is
  Odoo's own exchange-difference journal (a chart loaded with Czech active
  translates its code EXCH to KURZ), it keeps Odoo's names.

[19.0.1.2.0] — 2026-11-04
-------------------------

Changed
~~~~~~~

- One *Closing* menu under *Accounting → Accounting*: the currency
  revaluation and its reversal move under Odoo's own *Closing* (next to
  *Secure Entries*), and the second *Closing* menu that
  ``account_multicurrency_revaluation`` adds is hidden.

[19.0.1.1.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- The revaluation at the rate of the balance-sheet day is § 24c odst. 1
  písm. b) zákona o účetnictví, not "§ 24 odst. 6" (which does not exist).
  The user guide no longer says that Enterprise revalues a fixed-rate company
  at the fixed rate: ``l10n_cz_currency_revaluation_ee`` now reads the ČNB
  rate of the day as well.

[19.0.1.1.0] — 2026-09-28
-------------------------

Changed
~~~~~~~

- The revaluation runs with ``cssk_actual_rates``: a company on a fixed
  monthly rate (``currency_rate_update_cz``) is revalued at ČNB's actual rate
  of the revaluation date. Inert for a company on daily rates.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Thin bridge between the Czech chart (``l10n_cz``) and the OCA multicurrency-revaluation engine
  (``account_multicurrency_revaluation``): a post-init hook pre-fills the revaluation accounts with
  the Czech kurzové rozdíly accounts — **563** and **663**. Licensed AGPL-3 (depends on the AGPL
  OCA engine).
