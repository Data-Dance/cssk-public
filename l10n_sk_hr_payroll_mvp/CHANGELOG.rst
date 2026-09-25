=========
Changelog
=========

Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly SK MVP/MVPP (Mesačný výkaz poistného a príspevkov)
  with the aggregate ``poistne`` summary and the full per-employee annex,
  validated against the official ``MVPP-v2026.xsd``.
* Fund mapping np↔SICK, sp↔PENSION, ip↔DISABILITY, pvn↔UNEMPLOYMENT,
  up↔ACCIDENT, gp↔GUARANTEE, rfs↔RESERVEFUND, pfp↔SHORTTIME (employer/employee
  split via the ``*EMPLOYER`` / bare rule codes).

19.0.1.0.2 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* **Fix an over-stated social-insurance premium.** ``spoluPoistne`` was the sum
  of the payslip's ``SOCIALEMPLOYERTOTAL`` + ``SOCIALEMPLOYEETOTAL``
  categories, and those carry the HEALTH premiums too — ``HEALTH`` and
  ``HEALTHDOPLATOK`` sit in the ``SOCIALEMPLOYEE`` category, ``HEALTHEMPLOYER``
  in ``SOCIALEMPLOYER``. Health insurance is owed to the health insurers and
  reported separately on dávka 514, so the statement over-stated the premium
  due to the Sociálna poisťovňa and was internally inconsistent: the total
  exceeded the sum of its own fund rows. On a €2000 wage it reported €1012.00
  where €692.00 was due. It now sums the fund rows the form actually reports.
* The module's own test asserted the total against those same categories, so
  it ratified the defect rather than catching it. It now checks the total
  against the fund rows and separately asserts that health is excluded.

[19.0.1.0.3] — 2026-09-13
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

