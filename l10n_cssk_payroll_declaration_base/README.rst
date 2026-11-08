==============================================
CZ/SK Payroll e-Reporting — Declaration Base
==============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Engine-neutral base for Czech/Slovak payroll authority e-submissions: XSD-validated XML export, a submission state machine and an hr.payslip adapter that works on both the payroll and the hr_payroll engines.**

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

.. rubric:: Module facts

- **Technical name:** ``l10n_cssk_payroll_declaration_base``
- **Version:** 18.0.1.1.0
- **Licence:** AGPL-3
- **Requires:** ``hr``, ``mail``

Authors: Data Dance s.r.o.
