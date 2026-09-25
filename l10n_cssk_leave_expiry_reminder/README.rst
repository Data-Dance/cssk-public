==========================
Leave Expiry Reminder (CZ/SK)
==========================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: Other proprietary

|badge1|

Proactively reminds employees and HR about carried-over leave that is about to
expire. The Czech and Slovak statutory annual-leave (dovolená / dovolenka)
accrual plans set a carryover validity, so unused carried-over days are
forfeited about a year later (``carried_over_days_expiration_date`` on
``hr.leave.allocation``). Core Odoo only highlights this passively on the Time
Off dashboard; this module adds a proactive daily reminder.

This module is engine-neutral: it depends only on core ``hr_holidays`` and
therefore works with both the Enterprise ``hr_payroll`` and the
``payroll`` stacks.

.. contents::
   :local:

Features
========

* A daily scheduled action scans approved/confirmed allocations whose
  carried-over days expire within a configurable lead window and that still
  have days at risk. The figure reported is net of time off already taken
  against the allocation — core only performs that netting on the expiration
  date itself, so the stored ``expiring_carryover_days`` overstates it until
  then.
* For each, it schedules a dedicated **Expiring Leave** activity on the
  employee record, due on the expiration date, assigned to the employee's
  user (or the time-off approver / manager as a fallback).
* It optionally emails the employee's work address using a translatable mail
  template.
* Each cohort (identified by its expiration date) is reminded only once — a
  stored marker on the allocation deduplicates.
* Every channel is guarded independently: a missing user or email simply skips
  that channel and never breaks the cron.

Configuration
=============

Two system parameters (Settings ▸ Technical ▸ System Parameters):

* ``l10n_cssk_leave_expiry.lead_days`` — how many days ahead of expiry to start
  reminding. Default ``60``.
* ``l10n_cssk_leave_expiry.send_email`` — whether to also send the email.
  Default ``True``.

Credits
=======

Authors
~~~~~~~

* Data Dance s.r.o.

Maintainers
~~~~~~~~~~~

This module is maintained by Data Dance s.r.o.
