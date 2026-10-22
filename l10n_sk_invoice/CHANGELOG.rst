=========
Changelog
=========

All notable changes to **l10n_sk_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.1] — 2026-09-17
-------------------------

Fixed
~~~~~

- **``l10n_cssk_payment_symbols`` is now a declared dependency.** The module
  reads and writes the VS/KS/SS fields (``l10n_cssk_variable_symbol`` and
  siblings) but only received them transitively, through
  ``l10n_cssk_core``, which depended on the symbols module solely because
  the fields used to live there. Declaring it directly lets that legacy
  dependency be dropped from core without breaking this module.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak ``faktúra`` PDF layout carrying the mandatory §74 VAT-Act content on top of core + ``l10n_sk``.
- Party identifiers — customer **DIČ** printed next to the IČ DPH / IČO.
- Payment symbols — variabilný / konštantný / špecifický symbol (from ``l10n_cssk_core``).
- Statutory phrases auto-detected and printed in Slovak (+ English gloss): domestic reverse charge (prenesenie daňovej povinnosti, §69/12), intra-EU supply (§43) and export (§47) exemptions, plus a free-text manual note.
- Language-driven labels (Slovak for SK-language partners, English otherwise); statutory phrases always in Slovak per law.
