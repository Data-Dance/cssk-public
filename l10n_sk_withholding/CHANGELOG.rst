=========
Changelog
=========

All notable changes to **l10n_sk_withholding** are documented here.

[Unreleased]
------------

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
- Source reservations across live notices and full replacements, with retained
  exports taking precedence over later working drafts when filing is recorded.
  Actual-payment and physical-credit checks include reconciled income set-offs
  and registered payments through outstanding accounts.
- Retained filing after source, renderer or schema changes, including the common
  manual-channel path and binary-size UI context, native attachment integrity
  and access checks. The filed copy is never rewritten.
- Reviewed resident-title scope, regular-deadline warnings and retained evidence
  of authority-granted different deadlines; Slovak identifier date/mod11 checks.
- Native Slovak translations and explicit author-income guidance for an actually
  withheld art-fund contribution. Linked partial credit notes remain unsupported;
  the guide documents this limitation without an accounting bypass.
