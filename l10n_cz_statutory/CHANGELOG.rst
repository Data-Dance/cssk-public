=========
Changelog
=========

All notable changes to **l10n_cz_statutory** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.2] — 2026-09-13
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

[19.0.1.1.1] — 2026-09-13
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

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.3] — 2026-07-04
-------------------------

Fixed
~~~~~

- Fresh-install crash fixed: the finanční-úřad seed hook no longer fails on databases without
  the ``cs_CZ`` res.lang — the office name language is guarded (``cs_CZ`` if active, else the
  default). (Wave 1)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech statutory reference data for the country-neutral registries in ``l10n_cssk_core``:
  ``cssk.tax.authority`` (regional finanční úřady, c_ufo codes seeded from the official
  ``l10n_cz.tax_office`` codelist plus the Specializovaný finanční úřad) and ``cssk.person.type``
  (FO / PO taxpayer types).
- cs_CZ jsonb translations (i18n sweep).
