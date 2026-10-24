=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- **Two payments of one invoice in one statement import made the whole import
  fail** (cssk-public#9). OCA proposes a counterpart for every line of the
  batch first and reconciles afterwards, so both lines were given the
  invoice's full residual; the second reconcile raised *already reconciled*,
  and as this runs inside ``create()`` nothing from the import was saved,
  again on every re-pull. A line now finds only what earlier lines of the
  same import left open: a second full payment is left for a person, and one
  larger than what is left is proposed for the rest.

[19.0.1.0.0] — 2026-10-08
-------------------------

Added
~~~~~

- Initial release. Exact variable-symbol pass in OCA ``account_reconcile_oca``'s
  auto-reconciliation, running before OCA's label-in-reference invoice match.
  Leading-zero tolerant, bails out on an ambiguous symbol unless one document's
  open amount equals the transaction; a partial payment is reconciled, an
  over-payment only proposed. Foreign-currency lines are left to OCA and to
  a person.
