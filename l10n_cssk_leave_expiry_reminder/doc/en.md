---
title: Leave Expiry Reminder (CZ/SK)
summary: A daily reminder to employees about carried-over annual leave that their accrual plan will expire soon, as an activity and an email.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

An Odoo accrual plan can carry unused leave over to the next year and let the
carried-over days expire on a set date. The Slovak annual leave plans of the
payroll modules do that at the end of the following year; the Czech plans
carry leave over without any expiry. Odoo shows the expiry only passively, on the *Time Off*
dashboard. This module reminds people actively: once a day it looks for
carried-over leave that will expire soon and tells the employee, with an
activity and an email, how much is at stake and by when. The time-off
approver or the manager gets an activity of their own.

It depends only on Odoo's *Time Off* (`hr_holidays`), so it works with any
accrual plan that lets carried-over days expire, with either payroll engine
or without payroll at all.

## Legal background {#legal}

Neither country lets untaken annual leave lapse at the end of the following
year. What expires is the carried-over balance in Odoo, as set on the accrual
plan. The law instead obliges the employer to see that the leave is taken:

- **Czech Republic.** The employer must schedule leave that could not be
  taken in its year, or that was carried over at the employee's written
  request, so that it is taken **by the end of the following calendar year**
  ([§ 218 odst. 3 zákoníku práce](law:cz/2006/262)). If the employer has not
  scheduled it by **30 June** of the following year, the employee may schedule
  it too, with 14 days' written notice (§ 218 odst. 4). Leave that could not
  be taken even by the end of the following year because of sickness or
  maternity or parental leave is scheduled after the obstacle ends
  (§ 218 odst. 5).
- **Slovakia.** The employer must grant leave that could not be taken in its
  year so that it ends **by the end of the following calendar year**; if the
  employer has not scheduled it by **30 June** of that year, the employee may,
  with 30 days' written notice
  ([§ 113 ods. 2 Zákonníka práce](law:sk/2001/311#paragraf-113.odsek-2)).
  Leave prevented by maternity, paternity or parental leave, or by sickness,
  is granted after it ends
  ([§ 113 ods. 3 and 4](law:sk/2001/311#paragraf-113.odsek-3)).

The reminder is therefore a prompt to schedule the leave before the deadline
the employer has to meet. It asks the employee to agree with the manager when
the leave will be taken and says that annual leave does not lapse under the
Labour Code; the date it gives is the day the accrual plan removes the days
from the balance in Odoo.

## Setting it up {#setup}

Nothing has to be configured. Two system parameters change the behaviour
(*Settings → Technical → System Parameters*, developer mode):

| Parameter | Default | What it does |
|---|---|---|
| `l10n_cssk_leave_expiry.lead_days` | `60` | How many days before the expiry date the reminder is sent. |
| `l10n_cssk_leave_expiry.send_email` | `True` | Whether an email is sent in addition to the activity. `False`, `0`, `no` or `off` switch it off. |

The scheduled action *Time Off: Notify expiring carried-over leave (CZ/SK)*
runs once a day (*Settings → Technical → Scheduled Actions*). The email
template is *Time Off: Expiring Leave Reminder*; you may reword it.

For the reminder to reach the employee, the employee needs a **Related User**
(for the activity) and a **Work Email** (for the email). For HR to be told,
the employee needs a **Time Off** approver or a manager with a user.

## How the reminder works {#usage}

Every day the scheduled action takes the allocations that are *Approved*,
*To Approve* or *Second Approval* and whose carried-over days expire between today and today plus
the lead time (60 days by default). Allocations of an accrual plan that does
not allow a carry-over are left out: those are use-it-or-lose-it quotas
granted for the year, such as the Slovak family-care or doctor-visit days,
and nothing is carried over in them.

For each allocation it computes the days that would really be lost: the
carried-over balance less the leave taken from the allocation since. Odoo
itself does this subtraction only on the expiry date, so the figure the
reminder reports can be lower than the one stored on the allocation. If
nothing is left, no reminder is sent.

Otherwise it

1. schedules an **Expiring Leave** activity on the **employee** record, due on
   the expiry date, with the amount, the time-off type and the date, assigned
   to the employee's own user and addressed to the employee (*"You have …"*);
2. schedules a second **Expiring Leave** activity on the same record for the
   *Time Off Approver*, or if there is none for the user of the employee's
   manager, worded about the employee (*"<Employee> has …"*). This happens
   every time, also when the employee has a user and got the first activity.
   When the approver or the manager is the employee's own user, no second
   activity is created;
3. if enabled, emails the employee's *Work Email* with the same text, in the
   employee's language. For a time-off type requested in hours the amount is
   given in hours.

Each expiry date is reminded about **once**: the allocation remembers the date
it was last reminded for, and a new reminder comes only for a new carried-over
balance with a new expiry date. If nothing could be delivered — no user of
the employee, no approver or manager with a user, no work email — the
allocation is not marked as reminded, and the next daily run tries again.

With the Slovak plans of the payroll modules the carried-over days expire 364
days after the carry-over on 1 January, that is on 31 December of the
following year (30 December in a leap year), so by default the reminder comes
at the beginning of November. The Czech plans set no expiry, so their
allocations never get a reminder.

## Limitations {#limitations}

- **One reminder per expiry.** There is no second reminder closer to the
  date once a reminder has been delivered.
- The reminder is only as good as the accrual plan: an allocation without an
  accrual plan, or a plan without an expiry of carried-over days, never gets
  one.
- The sender of the email is the company email of the time-off type, or,
  when the time-off type has no company, the scheduled action's user.
