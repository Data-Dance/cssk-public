=========
Changelog
=========

All notable changes to **l10n_sk_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.3] — 2026-09-15
-------------------------

Fixed
~~~~~

- **``l10n_cssk_payment_symbols`` is now a declared dependency.** The module
  reads and writes the VS/KS/SS fields (``l10n_cssk_variable_symbol`` and
  siblings) but only received them transitively, through
  ``l10n_cssk_core``, which still depends on the symbols module solely
  because the fields used to live there. Declaring it directly lets that
  legacy dependency be dropped from core without breaking this module.

[19.0.1.0.2] — 2026-09-13
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

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak ``faktúra`` PDF layout carrying the mandatory §74 VAT-Act content on top of core + ``l10n_sk``.
- Party identifiers — customer **DIČ** printed next to the IČ DPH / IČO.
- Payment symbols — variabilný / konštantný / špecifický symbol (from ``l10n_cssk_core``).
- Statutory phrases auto-detected and printed in Slovak (+ English gloss): domestic reverse charge (prenesenie daňovej povinnosti, §69/12), intra-EU supply (§43) and export (§47) exemptions, plus a free-text manual note.
- Language-driven labels (Slovak for SK-language partners, English otherwise); statutory phrases always in Slovak per law.
