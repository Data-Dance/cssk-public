Engine-neutral foundation for the Czech payroll, shared by
``l10n_cz_hr_payroll_oca`` (OCA ``payroll``) and ``l10n_cz_hr_payroll_ee``
(Odoo Enterprise ``hr_payroll``).

It holds what does not depend on the payroll engine:

* the Czech payroll data of an employee on ``hr.version`` (agreement type,
  taxpayer declaration, ZTP/P and invalidity, children by tier, state-insured
  person, meal allowance, garnishment dependants, average hourly earnings,
  social insurance discount category), mirrored on ``hr.employee`` and
  whitelisted for contract templates of Czech companies;
* the statutory dovolená accrual plans (4 and 5 weeks per worked week, and the
  two archived "whole year on 1 January" alternatives), with translatable
  names.

Who may see and edit the fields is decided by the engine module, which
re-declares them with its own payroll-user group; this module sets only an
HR-manager floor.

The module also carries the user guide for the whole Czech payroll family.
