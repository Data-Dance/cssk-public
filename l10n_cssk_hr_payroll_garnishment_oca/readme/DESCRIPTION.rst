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
