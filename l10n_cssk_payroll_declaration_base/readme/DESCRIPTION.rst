This module is the shared foundation for the Czech and Slovak monthly payroll
authority e-submissions (social-insurance overviews). It ships:

* an **engine-neutral declaration sheet** (``cssk.payroll.declaration.mixin``)
  with a ``draft → generated → submitted`` state machine, period fields and an
  XSD-validated XML export pipeline;
* a **payslip adapter** (``_collect_payslip_totals``) that reads salary-line
  totals through the common ``hr.payslip`` read API shared by BOTH the
  ``payroll`` engine and the ``hr_payroll`` engine — the base depends
  on neither, resolving ``hr.payslip`` dynamically at runtime;
* a **version record** (``cssk.payroll.declaration.version``) carrying the QWeb
  template, XML root element and the official XSD, so a new form vintage is a
  data change rather than a code change.

Field and method names deliberately mirror Odoo's master
``hr.payroll.declaration.mixin`` so a future master (hr_payroll) port is a superclass
swap.

The concrete report modules (``l10n_cz_hr_payroll_pvpoj``,
``l10n_sk_hr_payroll_mvp``) build on this base.
