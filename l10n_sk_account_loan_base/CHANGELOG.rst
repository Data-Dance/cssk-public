=========
Changelog
=========

All notable changes to **l10n_sk_account_loan_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Gave the technical computed field an explicit ``string=``. Without one Odoo
  derives a label from the field name and exports it — "L10N Sk Jcd Is Sk
  Company" and the like — which is not English in any useful sense and cannot
  be translated into anything better. The field is a view modifier behind
  ``invisible="1"``, so no user reads it; the point is that it stops putting a
  mangled msgid in the catalogue.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- Slovak catalogue completed. Terms already stated in Slovak in the source are
  deliberately left untranslated — the source IS the translation, per the
  hybrid convention for these modules — so an empty ``msgstr`` there is correct
  rather than missing.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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
