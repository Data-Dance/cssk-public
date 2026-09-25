Bridge module: adds the statutory Slovak wage surcharges (mzdové zvýhodnenia)
and the minimum-wage top-up as salary rules on the OCA payroll engine.

All of the arithmetic and all of the dated statutory data live in
``l10n_sk_hr_payroll_priplatky``; this module only wires the rules into the
Slovak structure and mixes the payslip helpers into the engine's
``hr.payslip``. Installs automatically when both
``l10n_sk_hr_payroll_oca`` and the base are present.
