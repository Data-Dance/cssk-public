=========
Changelog
=========

All notable changes to **l10n_cz_account_cutoff** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Accruals of taxed lines no longer fail with "Missing 'Accrued Expense
  Tax Account'".** The OCA engine accrues the VAT as well by default and
  this chart has no account for it. *Accrual On Taxes* is now off for new
  companies, and switched off on install and on upgrade for existing
  companies that have no accrued-tax account configured (on the company or on a tax). Accruing
  the VAT would not be right either: input VAT cannot be deducted
  before the tax document is in hand (§ 73 odst. 1 písm. a) zákona 235/2004), so an accrual on 383 / 385 is
  the amount without VAT.

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Thin bridge between the Czech chart (``l10n_cz``) and the OCA cut-off/deferral engine
  (``account_cutoff_start_end_dates``): a post-init hook pre-fills the company's default cut-off
  accounts with the Czech časové rozlišení accounts — prepaid expense → **381**, deferred
  revenue → **384**, accrued expense → **383**, accrued revenue → **385** — so it works out of
  the box. Licensed AGPL-3 (depends on the AGPL OCA engine).
