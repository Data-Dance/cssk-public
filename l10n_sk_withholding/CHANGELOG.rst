=========
Changelog
=========

All notable changes to **l10n_sk_withholding** are documented here.

[Unreleased]
------------

[19.0.1.1.0] — 2026-11-16
--------------------------

Added
~~~~~

- Linked partial-credit capacity for original author bills and separate native
  liability journals; individual and shared limits across instalments, months,
  working drafts, retained snapshots and complete replacement corrections.
  Actual-payment cutoffs preserve earlier filings; native credit reversals can
  restore capacity. No accounting entry is rewritten by the source reader.
- Cumulative author income is validated at every actual payment date,
  independently of event creation order or the order in which months are filed.
  Alternative snapshots of a complete replacement reserve the greatest
  cumulative amount in their chain; unrelated notices consume the pool together.
- Capacity evidence is frozen for every relevant reservation date, including
  later dates of other notices. Retained filing reads those original facts;
  historical pre-feature exports retain their existing line and settlement
  safeguards instead of being reinterpreted through backdated credit notes.
- Czech translations of the new messages, and a guide note that a computed
  preview goes stale when another notice claims the same bill.

[19.0.1.0.1] — 2026-11-12
-------------------------

Fixed
~~~~~
- ``external_dependencies`` names the PyPI distribution ``python-stdnum``
  instead of the import name ``stdnum``. Odoo warned about the import name,
  and the tenant image's package check refused it.

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
- Czech translations and the user-guide entry under financial statements and
  income tax.
