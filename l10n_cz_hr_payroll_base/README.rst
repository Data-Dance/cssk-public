================================
Czech Republic — Payroll Base
================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1|

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

.. contents::
   :local:

Usage
=====

Nothing to configure. The module installs as a dependency of
``l10n_cz_hr_payroll_oca`` or ``l10n_cz_hr_payroll_ee``; the fields appear on
the forms those modules provide. See the user guide in
``static/description/index.html``.

Known issues / Roadmap
======================

* The salary rules, statutory figures, time-off types and the annual tax
  reconciliation stay in the engine modules: they are built on each engine's
  own models (``hr.rule.parameter``, work entry types or payroll codes,
  payslip input types), so they are not shareable as they stand.
* The annual tax reconciliation model is largely the same code on both
  engines; moving it here behind engine accessors is possible but would move
  a whole model with its table, and was left for a later step.

Credits
=======

Authors
~~~~~~~

* Data Dance s.r.o.

Contributors
~~~~~~~~~~~~

* Data Dance s.r.o.

  * Radovan Školník <radovan@skolnik.info>
