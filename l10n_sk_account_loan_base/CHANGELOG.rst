=========
Changelog
=========

All notable changes to **l10n_sk_account_loan_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Baseline: engine-neutral Slovak leasing/loan account defaults on ``res.company``,
  expressed as four **roles** (``long_term``, ``short_term``, ``interest``,
  ``leased_asset``) so that the Community and Enterprise bridges — whose engines name
  the same concepts differently — can share one Slovak mapping.
- Chart mapping: 474000 Záväzky z nájmu · 474100 Lízing (bežná časť) · 562000 Úroky ·
  022000 Samostatné hnuteľné veci.
- New companies wired from the chart template; existing SK companies via a post-init
  hook that fills only empty fields.
- Settings block under *Accounting*, hidden on non-SK charts.
- LGPL-3 so both the AGPL ``_oca`` bridge and the proprietary ``_ee`` bridge can
  depend on it.
