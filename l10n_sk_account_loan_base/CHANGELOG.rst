=========
Changelog
=========

All notable changes to **l10n_sk_account_loan_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- The four loan/lease *account* pickers in Settings listed other companies'
  accounts: Odoo drops a string domain when it copies a field into a related
  one.

[19.0.1.0.4] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The 60 % lease-term minimum rounds up.** It rounded to the nearest
  month, so a 43-month lease of a group 2 asset (60 % of six years is 43.2
  months) passed as a finančný prenájom. Group 2 now needs 44 months and
  group 4 needs 87.
- **Odpisová skupina 0** (two years, § 26 ods. 1) can be chosen.
- The depreciation-group labels no longer call the translation function at
  import (a warning in the server log); "4 roky", not "4 rokov".
- Description and README said the module is LGPL-3; it is AGPL-3,
  dual-licensed by its sole owner.

[19.0.1.0.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The VAT treatment of a lease is no longer presumed to be a supply of
  goods.** *Režim DPH* defaulted to goods, and with goods the instalment
  bills carry no VAT — so every lease of a Slovak company lost the VAT on its
  instalments, including operating leases and leases without a transfer of
  ownership, which are supplies of services taxed per instalment. A new lease
  now starts with no treatment and its instalments keep the taxes of their
  products until somebody chooses *Dodanie tovaru*. Leases created before this
  version keep the value they have; review them (see the user guide).

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
