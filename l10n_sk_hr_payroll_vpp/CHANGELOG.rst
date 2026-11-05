=========
Changelog
=========

Unreleased
~~~~~~~~~~

* **Fixed: a dohoda with regular income is no longer reported on the VPP.**
  The VPP took every DoVP and DoPČ payslip by agreement kind alone, so a
  monthly-paid DoPČ appeared both here (as ``ZECD2N``, irregular) and on the
  MVP (cssk-public#12). A payslip now reaches the VPP when its own contract
  version is a dohoda with *Regular monthly income* unset, which also brings
  in an irregular DoBPŠ (``ZECD3N``), left out before. The classification
  reads the version the payslip was computed on, so a later contract change
  does not move a past period. Still not covered: regular income paid after
  the insurance relationship ended (``ZECN``).

  *18.0 carry-over:* ``l10n_cssk-18.0`` has the same agreement-kind predicate.
  There the payslip's contract is ``hr.contract`` (``contract_id``), not
  ``hr.version``, so ``_payslip_version`` needs an 18.0 form.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.2] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.1.1] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Changed**

- **Slovak translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

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
