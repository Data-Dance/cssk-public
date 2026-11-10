=========
Changelog
=========

[18.0.1.3.0] — 2026-11-10
-------------------------

Added
~~~~~

- **Children for the child tax benefit** (``l10n.cz.employee.child``, on the
  employee): name, date of birth or birth number, ZTP/P, the order of the
  claim, and an optional *Claimed from* / *Claimed to*. A child counts in the
  month of birth and in every month of the claim (§ 35c odst. 10 ZDP); a
  ZTP/P child is doubled at its own order's amount (§ 35c odst. 7). Two
  children cannot be claimed as the first, or as the second, in the same
  months. The payslip and the annual tax reconciliation of both engines read
  the month's children from here; without any record they use the counts on
  the contract, as before. Ported from 19.0.1.2.0.

18.0 differences: the month helpers sit on ``hr.contract``; the
reconciliation reads the contract in force on each month's first day
(``hr.employee._l10n_cz_contract_at``: the latest running or closed contract
started by then, as 19.0's ``_get_version``).

[18.0.1.2.0] — 2026-11-09
-------------------------

Added
~~~~~

- Working pensioner discount field; one person's agreements add up for the insurance limit; from 2027 the annual meal and garnishment figures do not carry over from an earlier year. Ported from 19.0.

18.0.1.1.2 (2026-11-09)
=======================

Back-ported from 19.0: every change below, as released there.

18.0 differences: the fields live on ``hr.contract`` (19.0: ``hr.version``)
and the employee shows them read-only, edited on the contract form; the
module depends on ``hr_contract``; no contract-template whitelist (18.0 has
no contract templates); the accrual levels pin ``start_count`` to 0 and say
the carry-over through ``action_with_unused_accruals``.

[19.0.1.1.2] — 2026-11-08
-------------------------

Changed
~~~~~~~

- Guide: the 2027 statutory figures, what is not published yet, and the
  separate tax base of § 6 odst. 4 from 2027.

[19.0.1.1.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak catalogue: translated the strings that were still English.

[19.0.1.1.0] — 2026-10-27
=========================

Added
~~~~~

- **Short-time work compensation (§ 209) is a company setting**, under
  *Settings → Employees → Work Organization*, 100 % by default. Lower it only
  when an agreement with the trade union or an internal regulation sets a
  lower rate; payslips never pay less than the statutory 60 %.
- Shared helpers for both payroll engines: the health insurance premium
  (rounded up per employee, the employee's third rounded up, the minimum base
  top-up on the right side), the minimum base prorated by calendar days, and
  the 14-day limit of sickness compensation across consecutive sick-leave
  requests.

[19.0.1.0.0] — 2026-10-27
=========================

Added
~~~~~

- **Initial release: one shared base for both Czech payroll engines.** The
  Czech employee fields on the contract and the employee form (agreement type,
  taxpayer declaration, ZTP/P, invalidity, children, state-insured person,
  meal allowance, garnishment dependants, average hourly earnings, social
  insurance discount category), their contract-template whitelist and the
  statutory annual leave accrual plans used to be declared twice, once in the
  OCA and once in the Enterprise payroll module. They are now declared here
  once. Who may see the fields is still decided by the payroll module you run.
- **Existing databases keep everything.** Installing this module next to an
  already installed payroll module adopts that module's accrual plans in place,
  so allocations, assignments and translations stay attached to the same
  records; the employee data stays in the same columns.
- The user guide of the Czech payroll family now lives on this module's page.

