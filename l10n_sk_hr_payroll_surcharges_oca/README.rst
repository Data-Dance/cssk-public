======================================================
Slovakia — Wage Surcharges (príplatky) — OCA payroll
======================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Statutory Slovak wage surcharges and the minimum-wage top-up as salary rules for the OCA payroll engine.**

Bridge module: adds the statutory Slovak wage surcharges (mzdové zvýhodnenia)
and the minimum-wage top-up as salary rules on the OCA payroll engine.

All of the arithmetic and all of the dated statutory data live in
``l10n_sk_hr_payroll_surcharges``; this module only wires the rules into the
Slovak structure and mixes the payslip helpers into the engine's
``hr.payslip``. Installs automatically when both
``l10n_sk_hr_payroll_oca`` and the base are present.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_surcharges_oca``
- **Version:** 18.0.1.0.1
- **Licence:** AGPL-3
- **Requires:** ``l10n_sk_hr_payroll_oca``, ``l10n_sk_hr_payroll_surcharges``

Authors: Data Dance s.r.o.
