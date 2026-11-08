=========
Changelog
=========

Unreleased
----------

- *18.0 carry-over:* the Part IV / Part V routing, the row mapping and the
  2025 cutoff of rh2023 of 19.0.2.1.1 are not on 18.0 yet.

[19.0.2.1.1] — 2026-11-08
-------------------------

Fixed
~~~~~

- **Every employee was in the wrong part of the annex, and the advance in
  the insurance row.** HLASENIEv23 puts employees whose annual
  reconciliation this employer did not do in Part IV, and only those it did
  in Part V. Part IV now carries the month boxes, the employee's social and
  health insurance in their own rows and the withheld advance in its row.
  Part IV and Part V are counted and paginated independently.
- **No filing on the obsolete form.** The bundled HLASENIEv23 / rh2023
  edition now ends on 31 December 2025, on existing databases too (an
  upgrade migration), and the export refuses 2026 and later. The 2026 form
  gives the rows of Part V other meanings, so passing the old schema would
  not make a 2026 filing correct.
- **Incomplete annexes are refused.** An employee with an annual
  reconciliation done by this employer, or with a child tax bonus, needs
  data the module does not hold yet (the reconciliation's annual figures;
  the children's identities and months). The export stops for them rather
  than guessing from monthly totals. Engine bridges for both are exposed as
  extension points; the guide states which cases export today.

Contributed by votrelec (cssk-public#22).

Changed
~~~~~~~

* **Renamed from ``l10n_sk_hr_payroll_hlasenie`` to ``l10n_sk_hr_payroll_annual_tax_report``.** The technical
  name is English now, like every other module here; the statutory form keeps its
  Slovak name in the module title, in the models and in the data files, exactly as
  ``kv_dph``, ``eldp`` and ``pvpoj`` keep theirs. No migration ships with this: on a
  database that already has the old module installed, the old record stays behind
  with no code and the new module installs fresh, so rename the module record
  before upgrading if the old one holds data.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.0.4] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.2.0.3] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

Fixed
~~~~~

- **The house number is no longer taken from Street 2.** The employer's
  *číslo* was *Street 2* whatever it held (a building, a floor, a c/o line),
  and the house number stayed inside *ulica*. Both are now read by the shared
  helper of ``l10n_cssk_core``: the trailing number of *Street*, *Street 2*
  only when it holds nothing but a number.
- Časť V: the employee's house number is split off the private street into
  *c5cislo*, which was always empty.

**Changed**

- **Slovak translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

[19.0.2.0.2] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **Part III (rekapitulácia daňového bonusu) is filled.** Rows A, B and C were always empty, so a child tax bonus larger than the withheld advances — which row 5 may only report up to row 4 — appeared nowhere in the annual report. Row A is now the whole bonus paid, row B the part covered by the advances (row 5), row C the rest, paid from the company's own money.
- **Employee names.** Part V took the first word of the name as the first name and the last word as the surname, dropping anything in between. The surname is now the last word and the first name everything before it, and separate first/last name fields are used when a module provides them.

**Added**

- ``data/SCHEMA_VERSION`` pins the bundled ``rh2023.xsd`` (verified byte-identical to the Finančná správa copy on 2026-10-27), with a test that the bytes still match.


[19.0.2.0.1] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **pravnaForma** is filled from the company's *Právna forma* (recorded by l10n_sk_trade_registry). It called a method no module defines and was always empty.

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
