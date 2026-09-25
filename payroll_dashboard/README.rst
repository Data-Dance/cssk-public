==============================
Payroll Dashboard (lightweight)
==============================

Adds a **Dashboard** entry to the community Payroll app: a graph (headline
figures — gross, net, employer cost, income tax — per month) plus a pivot for
detail (employee × period × figure). No Enterprise widgets, no model changes —
it reuses the existing ``hr.payslip.line`` analytics.

Independent of any localization: depends only on the OCA ``payroll`` module.
