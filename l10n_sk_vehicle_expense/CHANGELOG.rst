=========
Changelog
=========

All notable changes to **l10n_sk_vehicle_expense** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a
Changelog. The ``19.0.x.y.z`` sections below are the 19.0 series' history,
kept verbatim.

[Unreleased]
------------

[18.0.1.0.2] — 2026-10-20
-------------------------

Fixed
~~~~~

- **The source files said "Other proprietary" while the manifest said
  AGPL-3.** The repository-wide relicensing of 2026-09-13 changed the manifest
  and dropped the AGPL text in beside it, but left the per-file headers of
  this module naming the proprietary licence. The module ships in
  ``cssk-public``, so the contradiction was published: ten files corrected to
  the AGPL-3 header 19.0 carries.

- Brought 19.0's 1.0.1 and 1.0.2 down: the explicit
  ``string="Slovak chart in use (technical)"`` on the computed view-modifier
  field — without one Odoo derives "L10N Sk Vehicle Is Sk Company" and exports
  that as a msgid — and the completed Slovak catalogue.

  Not ported, deliberately: 19.0's dependency on ``l10n_sk`` and its bare
  ``"21"``/``"20"``/``"28"`` tax-tag references. This series reaches those
  tags through ``l10n_sk_tax_report_backport`` and names them
  ``l10n_sk_tax_report_backport.tag_sk_21`` and so on, which is an 18.0-only
  adaptation, not a lag — the tags themselves are also named with the sign
  here ("+21"), which the test asserts.


[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- ``vs_auto_23`` / ``vs_auto_19`` — vehicle taxes whose repartition deducts only
  **50 %** of the VAT (§ 85n), the other half landing untagged on a non-deductible
  expense account so it reaches no row of the DPH return.
- Wizard on the vendor bill moving the non-tax share of fuel (**80 %** paušál,
  § 19 ods. 2 písm. l) bod 3) to that same account, without touching totals or VAT.
- Company settings for both ratios and the account, wired from the chart template
  and a post-init hook.
- 6 tests, incl. the assertion that only the deducted half carries tag 21.

Note on the rates
~~~~~~~~~~~~~~~~~

Built first against a 2017 Finančná správa guidance that gave **80 %** for both
sides, tied together by § 49 ods. 5. That is **obsolete**: the third consolidation
package (zák. **261/2025**, in force 1. 1. 2026) deleted § 49 ods. 5 and introduced
the § 85n flat **50 %** VAT deduction, while leaving the § 19 income-tax paušál at
80 %. The module was rebuilt around the two now-independent regimes. Dated sources
are worth re-checking before trusting a rate.
