# l10n_cssk_leave_expiry_reminder: developer notes

Not user documentation: this file is not rendered into a page.

## Netting

- A daily scheduled action scans approved/confirmed allocations whose
  carried-over days expire within a configurable lead window and that still
  have days at risk. The figure reported is net of time off already taken
  against the allocation — core only performs that netting on the expiration
  date itself, so the stored `expiring_carryover_days` overstates it until
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
