=========
Changelog
=========

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup (incl. ``l10n_sk_agreement_type`` now on the contract) was adapted to
  the 18.0 ``hr.contract`` API.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Slovak VPP (Výkaz poistného a príspevkov) for dohody /
  irregular income, with the aggregate ``poistne`` summary and the full
  per-employee annex, validated against the official ``VPP-v2026.xsd``.
* Scoped to dohoda contracts (``l10n_sk_agreement_type`` in ``dovp`` / ``dopc``)
  via the engine-neutral employee accessor; reuses the MVP fund → rule-code
  mapping. ``typZec`` defaults to the irregular-income variant (ZECD1N / ZECD2N).
