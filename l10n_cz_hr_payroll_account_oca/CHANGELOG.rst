=========
Changelog
=========

[19.0.1.1.1] — 2026-10-27
=========================

Fixed
~~~~~

- Loading the Czech chart no longer fails for a user without payroll rights (an accounting manager or settings administrator setting up a new company). OCA payroll gives such a user no write access to salary rules, so mapping their accounts raised an access error and aborted the chart. The mapping now runs as superuser.

[19.0.1.1.0] — 2026-10-27
=========================

Fixed
~~~~~

- **A company that loads the Czech chart after this module was installed is
  configured too**: the accounts are set on the Czech salary rules and the
  *Salaries* journal is created when the chart is loaded. Before, only the
  companies already on the Czech chart at installation got them.

[19.0.1.0.2] — 2026-10-27
=========================

Fixed
~~~~~

- **The child tax bonus, the annual tax settlement and the employer's
  social insurance discount are posted.** They had no accounts, so a bonus or
  refund paid to the employee never reached 331 and 342, and the discount
  never reached 524 and 336. They now post DR 342 / CR 331 and DR 336 /
  CR 524. Rules are found by their code in the Czech structure, and a code
  that resolves to nothing is logged. An upgrade maps the three rules for
  every company already on the Czech chart.
