=========
Changelog
=========

Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.0] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Added**

- The *Sociálna poisťovňa variable symbol* can be filled in on the VPP form. Generation requires it, but it was on no form anywhere.
- ``data/SCHEMA_VERSION`` pins the bundled schema, with a test that the bytes still match.


[19.0.1.0.2] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **spoluPoistne** is the sum of the social insurance fund rows the statement reports. It was the payslips' social category totals, which on both engines also carry the health insurance premiums, so the VPP over-stated the premium owed to the Sociálna poisťovňa.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Slovak VPP (Výkaz poistného a príspevkov) for dohody /
  irregular income, with the aggregate ``poistne`` summary and the full
  per-employee annex, validated against the official ``VPP-v2026.xsd``.
* Scoped to dohoda contracts (``l10n_sk_agreement_type`` in ``dovp`` / ``dopc``)
  via the engine-neutral employee accessor; reuses the MVP fund → rule-code
  mapping. ``typZec`` defaults to the irregular-income variant (ZECD1N / ZECD2N).
