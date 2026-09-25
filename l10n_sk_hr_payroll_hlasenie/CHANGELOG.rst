Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.2.0.0 (2026-09-16)
~~~~~~~~~~~~~~~~~~~~~~~

* **No longer declares ``res.company.l10n_sk_dic`` itself** — see the note in
  ``l10n_sk_hr_payroll_prehlad``'s changelog for the same version; this module
  carried the second of the two identical definitions. The field now comes from
  ``l10n_sk_base``, a new dependency, which owns the storage on ``res.partner``
  and migrates the old column. No data is lost.

19.0.1.1.0 (2026-08-06)
~~~~~~~~~~~~~~~~~~~~~~~

* **The Hlásenie can now be filed as opravné or dodatočné.** ``druhHlaseniaType``
  in the shipped XSD is three mutually exclusive flags — rh (riadne) / oh
  (opravné) / dh (dodatočné) — and all three were literals in the template, so
  only a riadne hlásenie could ever be produced. They are now driven by the
  shared ``correction_type``. There is no storno in the XSD, so it is not
  offered.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
~~~~~~~~~~~~~~~~~~~~~~~~~

* Initial release of the annual Slovak employer income-tax report **Hlásenie o
  vyúčtovaní dane a o úhrne príjmov zo závislej činnosti** (§ 39 ods. 9 zák.
  595/2003 Z. z.).
* Engine-neutral (built on ``l10n_cssk_payroll_declaration_base``; works with
  the ``payroll`` engine and the ``hr_payroll`` engine).
* Aggregates a full calendar year of payslips into the aggregate part
  (telo/cast1..cast3) and a full per-employee annex Časť V (telo/cast5, two
  employees per page).
* XML validated against the official Finančná správa schema ``rh2023.xsd``.

19.0.1.0.2 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* Read the engine-dependent salary-rule codes from
  ``l10n_cssk_payroll_declaration_base.rule_codes`` instead of restating
  them locally. No behaviour change; the local tuples were correct, but
  the knowledge now has one home rather than three.

[19.0.1.1.1] — 2026-09-13
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

