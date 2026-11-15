=========
Changelog
=========

All notable changes to **l10n_cz_account_move_template** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-11-15
-------------------------

Added
~~~~~

- Six starter předkontace for interní doklady on the ``l10n_cz`` chart, as
  editable ``account.move.template`` records: the four legs of a transfer
  between pokladna and bankovní účet through 261 Peníze na cestě, and the
  přeúčtování of the approved result from 431 (zisk to 428, ztráta to 429).
  The Czech counterpart of ``l10n_sk_account_move_template``.
- The money-in-transit templates use the company's Liquidity Transfer account
  and the accounts of its bank and cash journals, not 261000 (the chart's bank
  suspense account) or the summary accounts 221000 / 211000.
- Loaded with the chart, and on install for companies that already have it;
  only templates a company lacks are created, so an accountant's edit is never
  reverted.
