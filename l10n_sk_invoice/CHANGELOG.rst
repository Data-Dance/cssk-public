=========
Changelog
=========

All notable changes to **l10n_sk_invoice** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- **The module no longer installs on an Odoo 19.0 newer than 2026-10-14.**
  ``vat_registry_tax_id_external_layout_label`` removed ``l10n_sk``'s duplicate
  supplier VAT line with ``<xpath expr="//li[span[@t-out='company.vat']]">``.
  Odoo removed that line itself in 135758684, so the xpath matched nothing and
  the install died with *Element ... cannot be located in parent view*. The
  xpath is gone; upstream does the job now. On an Odoo 19.0 older than that
  commit the supplier VAT prints twice again — update Odoo rather than
  restoring the xpath, which breaks every current build.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **§43 vs §15 statutory note (2026-09-27).** The same compute exists on
  18.0 (``models/account_move.py``: ``§43`` for any 0 % EU line). Port
  ``_l10n_sk_zero_rated_kinds`` and its tests; check 18.0's ``l10n_sk`` tax
  xmlids (``vy_eu_s`` / ``vy_eu_t``) before relying on them.

- **Duplicate IČ DPH in the header (19.0.1.0.6) is owed to 18.0.** 18.0's
  l10n_sk header block has the same VAT line next to core's; port the extra
  xpath in ``report/report_registry_label.xml`` and
  ``test_supplier_vat_is_printed_once``.

- **IČO label (19.0.1.0.5).** DISCHARGED 2026-11-02 — do not port this
  again: ported as 18.0.1.0.2. The six "ID:" nodes print
  ``company_registry_label`` on 18.0 as well.

[19.0.1.1.0] — 2026-11-09
-------------------------

Added
~~~~~

- Warning on cash payments above 5 000 € (§ 4 zákona 394/2012 Z. z.), adding together earlier cash payments of the same invoices (§ 6 ods. 2).

[19.0.1.0.8] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.0.6] — 2026-11-03
-------------------------

Fixed
~~~~~

- The supplier's IČ DPH was printed twice in the invoice header: every
  Odoo layout already prints the company VAT, and core l10n_sk added its own
  line. l10n_sk's line is dropped (the folded layout, which has no core VAT
  line, keeps it).

[19.0.1.0.5] — 2026-11-02
-------------------------

Fixed
~~~~~

- Invoices print **IČO** before the company registry number of the supplier
  and the customer. Core l10n_sk hardcodes "ID:" in six places (and its own
  sk.po translates it as "ID:"); they now print the party's
  ``company_registry_label`` - IČO for Slovak and Czech parties through
  l10n_cssk_core, the core label for other countries.

[19.0.1.0.4] — 2026-09-27
-------------------------

Fixed
~~~~~

- **A zero-rated service to an EU customer printed the §43 goods exemption.**
  The note keyed on "a 0 % tax and an EU customer with a VAT number", so a B2B
  service — taxed in the customer's state under §15 ods. 1 with the customer
  liable — was described as an exempt intra-Community supply of goods, next to
  core's own "článok 196" reverse-charge note that says the opposite. Goods
  and services are now told apart by the tax's scope (``0% EU M`` /
  ``0% EU S``), falling back to the product type; a mixed invoice prints both
  phrases. The triangular ``0% EU T`` no longer gets §43 (core's article 141
  note stands), and §47 is cited only for exported goods, since a service to a
  non-EU customer is outside Slovak VAT rather than exempt.

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
