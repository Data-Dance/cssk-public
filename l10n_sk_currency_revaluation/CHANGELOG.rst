=========
Changelog
=========

All notable changes to **l10n_sk_currency_revaluation** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- revaluation journal = the chart's exch journal (template + hook) — 19.0.1.3.0.
- Accountant role implies group_revaluation_additional (data/security.xml);
  KURZ named in sk/cs/en — 19.0.1.2.0. Check 18.0 has the same OCA group
  first.

[19.0.1.3.0] — 2026-11-04
-------------------------

Changed
~~~~~~~

- **Revaluation goes through the company's exchange-difference journal.** A
  Slovak chart now sets ``currency_reval_journal_id`` to the chart's ``exch`` journal, and
  the install hook uses an existing KURZ or that journal before it creates a
  new KURZ. Before, a chart loaded with English active (code EXCH) ended up
  with two exchange journals: Odoo's and our KURZ. Existing companies keep
  the journal they have.

[19.0.1.2.0] — 2026-11-04
-------------------------

Fixed
~~~~~

- **Nobody saw the revaluation menus.** account_multicurrency_revaluation
  shows *Currency Revaluation* and *Reverse Currency Revaluation* only to its
  group *Additional provisioning entries posting*, which no role implied. The
  *Accountant* role (*Hlavný účtovník*) now implies it, for existing members
  too.
- **The KURZ journal had only its Slovak name**, stored as the English one;
  it is now *Kurzové rozdiely* / *Kurzové rozdíly* / *Exchange Rate
  Differences*. The upgrade renames it unless you renamed it. Where KURZ is
  Odoo's own exchange-difference journal (a chart loaded with Slovak active
  translates its code EXCH to KURZ), it keeps Odoo's names.

[19.0.1.1.0] — 2026-11-04
-------------------------

Changed
~~~~~~~

- One *Closing* menu under *Accounting → Accounting*: the currency
  revaluation and its reversal move under Odoo's own *Closing* (next to
  *Secure Entries*), and the second *Closing* menu that
  ``account_multicurrency_revaluation`` adds is hidden.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: thin chart-preset bridge pre-filling the OCA multicurrency-revaluation accounts with the Slovak **563** / **663** (kurzové rozdiely) accounts. AGPL-3 (depends on the AGPL OCA engine); mapping applied via post-init hook.
