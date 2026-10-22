=========
Changelog
=========

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added Czech (``i18n/cs.po``) and Slovak (``i18n/sk.po``)
  translations of the declaration/period/state-machine/XSD terminology.

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. The declarative ``models.Constraint`` (19.0) on the
  per-employee annex is expressed via ``_sql_constraints`` for 18.0. The
  engine-neutral payslip adapter (``_collect_payslip_totals``) is unchanged.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release.
* ``cssk.payroll.declaration.mixin`` — engine-neutral declaration sheet with a
  ``draft → generated → submitted`` state machine and an XSD-validated XML
  export pipeline.
* ``cssk.payroll.employee.declaration`` — per-employee annex source.
* ``cssk.payroll.declaration.version`` — form-vintage record carrying the QWeb
  template, root element and the shipped XSD.
* ``_collect_payslip_totals`` payslip adapter reading the common ``hr.payslip``
  API shared by the ``payroll`` and the ``hr_payroll`` engines
  (no dependency on either).
