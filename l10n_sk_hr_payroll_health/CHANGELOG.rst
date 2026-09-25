=========
Changelog
=========

Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.1.0 (2026-09-16)
~~~~~~~~~~~~~~~~~~~~~~~

* **The dávka 514 no longer files without a DIČ.** ``_preflight`` checked the
  IČO, the health payer number and the target insurer, but not the DIČ, while
  ``_declaration_render_context`` read it as
  ``self._digits(getattr(company, "l10n_sk_dic", ""))[:12]`` — a ``getattr``
  default and a ``_digits`` that turns a missing value into ``""``. So a company
  with no DIČ produced an empty ``<CompanyIDTaxCode>`` and the dávka went to the
  health insurer with nothing in it, no error raised and no warning logged. The
  Prehľad and the Hlásenie have always refused in that situation; this one did
  not. It now refuses too, with the same message.

* Depends on ``l10n_sk_base``, which owns the DIČ field this module reads.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly SK dávka 514 (Mesačný výkaz preddavkov na poistné)
  for VšZP / Dôvera / Union — root ``MZSR`` following the official
  ``514-2023.xsd`` element model: Identification + CorporateBody + InsuranceBody
  aggregate + one PersonData row per employee. Insurer code (25/24/27) is
  company config / a per-declaration selection.
* Rule mapping DepositOfEmployer↔HEALTHEMPLOYER, DepositOfEmployee↔HEALTH,
  DepositOffEmployeeAdd↔HEALTHDOPLATOK / HEALTH_DOPLATOK.
* Ships and loads the official ``514-2023.xsd``, but runs it as a non-fatal
  check: the published schema is internally defective (single-char ``[0-9]``
  patterns under multi-char minLength, impossible integer bounds) so no real
  instance can pass ``assertValid``; the authoritative gate is well-formedness
  + structural conformance to its element model.

19.0.1.0.2 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* Read the engine-dependent salary-rule codes from
  ``l10n_cssk_payroll_declaration_base.rule_codes`` instead of restating
  them locally. No behaviour change; the local tuples were correct, but
  the knowledge now has one home rather than three.
