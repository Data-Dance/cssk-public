================================================
CZ/SK Wage Garnishment — payroll engine bridge
================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Apply the Czech/Slovak wage-garnishment waterfall on payslips computed by the OCA payroll engine.**

Wires the CZ/SK wage-garnishment register into the OCA ``payroll`` engine.

The module itself is deliberately tiny: it mixes
``cssk.garnishment.payslip.mixin`` into this engine's ``hr.payslip`` and hooks
the payslip lifecycle, so that confirming a payslip writes the per-order
deduction ledger and cancelling or resetting it takes those rows back out
(leaving anything already remitted to the bailiff alone).

The amount itself is already correct with the base module alone — the country
salary rules call into the register directly. This bridge is what records
*which order* got *how much*, which is what the remittance and the statutory
account of deductions are built on.

.. rubric:: Module facts

- **Technical name:** ``l10n_cssk_hr_payroll_garnishment_oca``
- **Version:** 18.0.1.0.0
- **Licence:** AGPL-3
- **Requires:** ``payroll``, ``l10n_cssk_hr_payroll_garnishment_base``

Authors: Data Dance s.r.o.
