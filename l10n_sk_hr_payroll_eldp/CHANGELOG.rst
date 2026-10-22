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

* Initial release: annual Slovak ELDP (Evidenčný list dôchodkového poistenia),
  one ``eldpZec`` per employee with the year's pension assessment base and
  insured period, validated against the official ``ELDP-v2015_1.3.xsd``.
* Reuses the engine-neutral payslip adapter over a whole-year period; the
  pension base ``vzDP`` is derived from the summed GROSS.
