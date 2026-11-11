=========
Changelog
=========

All notable changes to **l10n_sk_withholding** are documented here.

[Unreleased]
------------

Fixed
~~~~~

- Refuse reversed source entries and reserve source allocations across live
  notices and full replacements, including concurrent changes in other months.
- Record actual filing from retained exports, with current-source drift warnings
  and the common manual-channel path, without rewriting the filed copy.
- Retain filing after renderer/schema upgrades and with binary-size UI context;
  verify native attachment integrity and preserve access errors.
- Validate Slovak identifier dates/length/mod11 and actual settlement capacity.

Added
~~~~~

- Reconciled income set-offs and native registered payments through outstanding
  accounts, with retained actual-payment evidence and physical credit references.
- Complete resident-title scope confirmation, regular-deadline warnings and
  evidenced authority-granted different deadlines.

Changed
~~~~~~~

- Separate stored/name and end-date computes; randomise committed test fixtures;
  retain original XSD bytes under data; export native Slovak error translations.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- Not yet ported. Carry the common workflow seam and the complete native source,
  reservation, settlement, filing and identity lifecycle with their tests.


[19.0.1.0.0] — 2026-11-10
--------------------------

Added
~~~~~

- OZN4311v26 for reviewed domestic individual dividends from profit periods
  starting in 2017 or later, and resident author income without a withholding
  waiver. Native posted ledger sources; no additional accounting entries.
- Annex A uses two income slots per page. Profit-period rates, mathematical
  cent rounding and actual remittance allocations are separate facts.
- Reviewed correction filing dates, complete replacement corrections, frozen
  filed XML/source history and shared submission/receipt tracking.
- Ordinary-accountant access, company isolation and protected workflow fields.
