=====================================
Payroll Worked Days & Inputs Timeline
=====================================

Adds **timeline**, **pivot** and **list** views for the payslip *worked days*
and *other inputs*, per employee over time — a community (OCA ``web_timeline``)
alternative to the Enterprise "work entries" gantt for reviewing the inputs
that fed each payroll calculation.

It stores ``employee_id`` / ``date_from`` / ``date_to`` mirrors on
``hr.payslip.worked_days`` and ``hr.payslip.input`` so those lines can be
grouped, pivoted and placed on a timeline in their own right.

This module is **independent** of any localization: it depends only on the OCA
``payroll`` and ``web_timeline`` modules.

Usage
=====

*Payroll → Worked Days Timeline* — timeline grouped by employee; switch to pivot
(employee × month × hours/days) for an audit matrix.

*Payroll → Other Inputs* — pivot / list of the numeric input lines.
