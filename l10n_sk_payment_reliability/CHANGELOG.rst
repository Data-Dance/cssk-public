=========
Changelog
=========

All notable changes to **l10n_sk_payment_reliability** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-27
-------------------------

Added
~~~~~

- **Zoznam platiteľov DPH, u ktorých nastali dôvody na zrušenie registrácie**
  (§ 81 ods. 4 písm. b) ZDPH), from the FS open-data API. The dataset slug
  ``ds_dphz`` and its ``ic_dph`` column are **not verified against the live
  API** (it needs a key and none was at hand), so the module first asks
  ``/lists/ds_dphz`` which columns are searchable and reports the check as
  *unavailable* — never as a clean record — when that does not confirm it.
  Verify with a real key before relying on it.

Fixed
~~~~~

- Two tests had never run: ``setUpClass`` died on the IČO ``12345678``, which
  fails the checksum ``l10n_cssk_core`` enforces since 19.0.1.7.0, and a
  German fixture VAT failed ``base_vat`` once it was reached.

[19.0.1.0.3] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

[19.0.1.0.2] — 2026-09-13
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

[19.0.1.0.1] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak country provider for ``l10n_cssk_payment_reliability`` against the FS open-data API (``iz.opendata.financnasprava.sk``).
- **Registered bank accounts** — dataset ``ds_dph_iban`` (accounts a VAT payer notified to the tax authority), looked up by IČ DPH.
- **Tax reliability index** — dataset ``ds_iz_ran`` (index daňovej spoľahlivosti: vysoko spoľahlivý / spoľahlivý / menej spoľahlivý), looked up by IČO.
- Requires an FS open-data API key (Settings → Accounting); the provider is inert and reports "not checked" without one.
