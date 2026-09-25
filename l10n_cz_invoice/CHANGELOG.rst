=========
Changelog
=========

All notable changes to **l10n_cz_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-09-15
-------------------------

Fixed
~~~~~

- **``l10n_cssk_payment_symbols`` is now a declared dependency.** The module
  reads and writes the VS/KS/SS fields (``l10n_cssk_variable_symbol`` and
  siblings) but only received them transitively, through
  ``l10n_cssk_core``, which still depends on the symbols module solely
  because the fields used to live there. Declaring it directly lets that
  legacy dependency be dropped from core without breaking this module.

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Czech screen. The template and the catalogues now carry them,
  and the Czech is written.

Fixed
~~~~~

- **The customer DIČ line is gone — core already prints it.**
  ``account.report_invoice_document`` outputs the counterparty's ``vat`` under
  ``company.account_fiscal_country_id.vat_label``, and Czechia's is **DIČ**
  (``res.country`` CZ carries ``{"cs_CZ": "DIČ", "en_US": "VAT"}``). This
  module added a second line for the same identifier.

  The duplication was invisible while that line rendered ``l10n_cssk_dic``, a
  separate field holding the same number without its country prefix. Verified
  on a rendered invoice: the VAT number now appears exactly once, and a test
  pins that.

  Slovakia is the case that genuinely needs two lines — DIČ and IČ DPH are
  different identifiers there — and that field now lives in ``l10n_sk_base``.

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

- Czech statutory invoice content on top of core + ``l10n_cz``: customer DIČ (from
  ``l10n_cssk_core``), payment symbols (variabilní / konstantní / specifický symbol).
- Auto-detected statutory phrases: domestic reverse charge (§92a), intra-Community supply (§64),
  export (§66), plus a free-text manual note.
- cs_CZ jsonb translations (i18n sweep, 2026-06-30).
