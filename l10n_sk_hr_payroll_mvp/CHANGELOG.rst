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

* Initial release: monthly SK MVP/MVPP (Mesačný výkaz poistného a príspevkov)
  with the aggregate ``poistne`` summary and the full per-employee annex,
  validated against the official ``MVPP-v2026.xsd``.
* Fund mapping np↔SICK, sp↔PENSION, ip↔DISABILITY, pvn↔UNEMPLOYMENT,
  up↔ACCIDENT, gp↔GUARANTEE, rfs↔RESERVEFUND, pfp↔SHORTTIME (employer/employee
  split via the ``*EMPLOYER`` / bare rule codes).
