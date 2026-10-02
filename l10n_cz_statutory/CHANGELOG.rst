=========
Changelog
=========

All notable changes to **l10n_cz_statutory** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.3.0] — 2026-09-29
-------------------------

Changed
~~~~~~~

- Depends on ``partner_nace``: the company's activity code for the returns is
  its partner's NACE code.

Fixed
~~~~~

- The competent-office preflight (``c_ufo``) applied to every Czech
  submission, so an OSS return could not be exported where this module is
  installed — although OSSEI1 carries no ``c_ufo`` at all. A form now
  declines it through ``_cz_requires_tax_authority()``.

[19.0.1.2.0] — 2026-09-28
-------------------------

Added
~~~~~

- **Bad-debt VAT corrections** — ``account.move.l10n_cz_bad_debt``: *P* for a
  correction under § 46 and following (creditor) or § 74b (debtor, § 74a
  before 2025), *A* for the old § 44, which a constraint allows only when the
  corrected supply is dated up to 31. 3. 2019. On the invoice's *Other Info*
  page, readonly once posted. The taxes stay the ordinary ones; the flag is
  what the VAT return and the kontrolní hlášení read.

- **Who files, once for every Czech EPO VAT form.**
  ``res.company._l10n_cz_epo_vetap()`` builds the ``VetaP`` of DPHDP3, the
  kontrolní hlášení and the souhrnné hlášení, which used to carry only the
  DIČ, the office and the name with ``typ_ds="P"`` hard-coded:

  * ``typ_ds`` follows the company's person type, so a natural person files
    as **F** with titul / jméno / příjmení instead of an obchodní jméno;
  * the seat address (ulice, číslo popisné / orientační split off the street,
    obec, PSČ without spaces), telephone and e-mail;
  * the **oprávněná osoba** (name and vztah k právnické osobě) and who
    **sestavil** the filing;
  * a **zástupce** filing for the client — typically a tax adviser — with the
    kód podepisující osoby, IČO or name, and evidenční číslo / datum narození.

  Set on the company form, page *EPO podání*. Sizes and codes are the XSDs'.
- ``res.company._l10n_cz_typ_platce(date)``: the DPHDP3 ``typ_platce``, "P"
  unless a module recording the company's VAT status says otherwise.

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
