=========
Changelog
=========

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.0.0 (2026-07-08)
=======================

* Initial release. A daily scheduled action reminds employees and HR about
  carried-over leave that is about to expire (the CZ/SK carryover-validity
  forfeit): it schedules an *Expiring Leave* activity on the employee and
  optionally emails the employee, with per-cohort deduplication and
  configurable lead time. Depends only on core ``hr_holidays``.

[19.0.1.0.3] — 2026-08-05
-------------------------

Fixed
~~~~~

- Statutory use-it-or-lose-it quotas are no longer in scope. A SK §141
  doctor-visit or sprevádzanie allowance (and OČR) is granted whole on 1
  January and simply lapses — nothing is ever *carried over*, and telling an
  employee to go book seven doctor visits before December is nonsense. The
  cron now skips allocations whose accrual plan has ``can_be_carryover=False``,
  which is exactly that switch (core derives ``action_with_unused_accruals =
  'lost'`` from it). Plan-less regular allocations stay in scope; they never
  carry an expiration date anyway.

[19.0.1.0.2] — 2026-08-05
-------------------------

Fixed
~~~~~

- The reminder now reports the days that will *actually* be forfeited instead
  of the whole carried-over balance. ``expiring_carryover_days`` is the gross
  figure captured on the carryover date; core only nets it against time off
  since taken once the expiration date is reached. An employee who carried 5
  days and had since taken 2 was told 5 days would expire, and one who had
  used all of them was reminded anyway. New helper
  ``_l10n_cssk_net_expiring_days()`` mirrors the netting
  ``_process_accrual_plans`` does, including the hours-to-days conversion for
  hour-unit leave types, and allocations with nothing left at risk are now
  skipped without being marked as reminded.
- The reminder email quoted the same gross field independently of the activity
  and hardcoded the word "day(s)". Both now come from the shared helper, so
  the two channels can no longer disagree and an hour-unit leave type is
  worded correctly. A post-migration rewrites the ``noupdate`` template on
  existing databases (leaving a customised body alone), and the Czech and
  Slovak translations of the body were updated to match.

[19.0.1.0.1] — 2026-07-18
-------------------------

Fixed
~~~~~

- The reminder template now renders in the employee's language
  (``lang = {{ object.employee_id.user_id.lang or object.employee_id.lang }}``)
  instead of the sending user's. A post-migration backfills the ``noupdate``
  record on existing databases.

