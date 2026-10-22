=========
Changelog
=========

18.0.1.1.0 (2026-08-08)
=======================

Backported from 19.0.

* **Fixed: the reminder quoted the whole carried-over balance.**
  ``expiring_carryover_days`` is the gross figure captured on the carryover
  date; core only nets it against time off since taken once the expiration
  date arrives. Someone who carried 5 days and had taken 2 was told 5 would
  expire, and someone who had used them all was reminded anyway.
* **Statutory use-it-or-lose-it quotas are out of scope.** A §141 doctor-visit
  allowance is granted whole on 1 January and simply lapses — nothing is
  carried over, and telling an employee to book seven doctor visits before
  December is nonsense. Filtered in Python rather than in the domain, because
  the two Odoo versions spell it differently: 19.0 has
  ``hr.leave.accrual.plan.can_be_carryover``, 18.0 only the level's
  ``action_with_unused_accruals``, which 19.0 derives from that flag. The
  helper probes for whichever exists, so the same code runs on both.

18.0.1.0.0 (2026-07-08)
=======================

* Initial release. A daily scheduled action reminds employees and HR about
  carried-over leave that is about to expire (the CZ/SK carryover-validity
  forfeit): it schedules an *Expiring Leave* activity on the employee and
  optionally emails the employee, with per-cohort deduplication and
  configurable lead time. Depends only on core ``hr_holidays``.

[18.0.1.0.1] — 2026-07-18
-------------------------

Fixed
~~~~~

- The reminder template now renders in the employee's language
  (``lang = {{ object.employee_id.user_id.lang or object.employee_id.lang }}``)
  instead of the sending user's. A post-migration backfills the ``noupdate``
  record on existing databases.

