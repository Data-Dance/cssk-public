=========
Changelog
=========

All notable changes to **l10n_sk_jcd** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.4] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

[19.0.1.1.3] — 2026-09-13
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

[19.0.1.1.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- Gave the technical computed field an explicit ``string=``. Without one Odoo
  derives a label from the field name and exports it — "L10N Sk Jcd Is Sk
  Company" and the like — which is not English in any useful sense and cannot
  be translated into anything better. The field is a view modifier behind
  ``invisible="1"``, so no user reads it; the point is that it stops putting a
  mangled msgid in the catalogue.

[19.0.1.1.1] — 2026-09-13
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

[19.0.1.1.0] — 2026-08-20
-------------------------

Fixed
~~~~~

- A declaration entered for an earlier period was taxed at **today's** rate.
  ``vat_rate`` names a band by its current rate and the tax was resolved by a
  fixed xmlid, so a 2019 import in the standard band posted 23 % instead of
  20 %. The base is what the customs office assessed, so only the tax figure
  moved — silently, and by three points. The band is now resolved by xmlid and
  the rate within it by the declaration's date, through the historical-rate
  clones of ``l10n_cssk_vat_return_base``. Without that module installed there
  are no clones and behaviour is unchanged.

Added
~~~~~

- ``vat_rate_effective`` — the rate actually applied, shown on the form beside
  the band. ``vat_amount`` is computed from it rather than from the band's
  label, so the figure on the document and the tax that posts cannot disagree.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Baseline: ``l10n.sk.jcd``, the Slovak import customs declaration as an accounting
  document — colná hodnota, clo, iné colné poplatky, VAT base and rate, regime,
  links to the supplier invoices and the goods receipts.
- Duty capitalised into stock value via ``stock.landed.cost``.
- Import VAT posted through the ``l10n_sk`` core taxes, so the existing tag-driven
  VAT return reports it with no new engine: ``vs_cust_*`` → r22/r22a/r23,
  ``vs_imp_post_*`` → r11c–e / r12c–e / r23a–c.
- **Deduction gate**: posting is refused without an MRN and an attached customs
  document (DPHv25 poučenie bod 38, § 49 ods. 2 písm. d)).
- Notional base posted +/- on a clearing account so only VAT and duty are real.
- Clearing account (379000) and duty product wired from the chart template for new
  SK companies, and by a post-init hook for existing ones.
- 12 tests, incl. exact DPH tag assertions for both regimes and duty reaching the
  stock valuation.

Notes
~~~~~

- Two Odoo 19 differences hit while building: ``mail.thread`` no longer has
  ``message_main_attachment_id`` (so the customs-document check is evaluated on
  read, not via ``@depends``), and ``stock.move`` has no ``name`` field
  (``_rec_name = 'reference'``).
- Landed costs are only permitted on FIFO/AVCO categories; duty capitalisation does
  not apply to standard-cost products.
