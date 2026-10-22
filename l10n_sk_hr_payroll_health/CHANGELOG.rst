=========
Changelog
=========

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API.

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
