=========
Changelog
=========

[19.0.1.2.0] — 2026-10-27
=========================

**Fixed**

- The Dashboard tiles are **per company**: each company selected in the company switcher gets its own tiles in its own currency, and a user no longer sees the payroll totals of companies they have no access to.
- Only **done** payslips are counted; drafts, payslips waiting for verification and cancelled payslips used to be added in.
- The employer-contribution, labour-cost and income-tax tiles now also read the **Czech** payroll totals (``SOCIALERTOT`` + ``HEALTHERTOT`` + ``SOCIAL_DISCOUNT``, ``INCOMETAXTOT``); with Czech rules they showed nothing or the gross wage only. The Analysis filters were extended the same way.

**Added**

- Slovak and Czech translation; the tile names are now translatable.
- Analysis opens on **done** payslips of the selected companies (filter *Done payslips*, removable).

19.0.1.0.0 (2026-07-09)
=======================

* Initial release: graph + pivot payroll dashboard on ``hr.payslip.line``.
