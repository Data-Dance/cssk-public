# hr_attendance_holidays_kiosk: developer notes

Not user documentation: this file is not rendered into a page.

Bridge module (`hr_attendance` + `hr_holidays`) that lets employees pick a
**reason for leaving** when they check **out** at the public attendance kiosk —
the CZ/SK "přerušení / prerušenie práce" workflow.

## What it does

1. Adds **Show in Attendance Kiosk** (`kiosk_visible`) + **Kiosk Order**
   (`kiosk_sequence`) to Time Off Types. A reorderable **Time Off →
   Configuration → Kiosk Reasons** list lets you set the order, name and colour;
   the colour is shown on the reason button (with auto-contrasting text — colour
   0 "No color" keeps the default light button).
2. After the employee identifies at the kiosk (badge scan **or** manual
   selection / PIN), if the next action is a **check-out** and at least one
   kiosk-visible reason exists, a reason screen appears:
   - a default **Work ended** button → normal check-out, nothing extra;
   - one button per kiosk-visible Time Off Type.
3. Picking a real reason:
   - records the check-out,
   - tags the attendance (`checkout_reason_id`),
   - creates a **draft (To Approve)** time off from the check-out time to the
     end of the working day, linked back via `checkout_leave_id`, for HR to
     finalize/approve.

Check-**in** stays single-scan, with two exceptions handled automatically:

- **Same-day return:** when the employee checks back in the same day, the still-
  draft departure leave is shortened to the check-in time, so it covers only the
  actual time away (not the whole rest of the day). Already-approved leaves are
  left untouched.
- **After an automatic check-out:** if the previous segment was closed by the
  core *Automatic Check Out* cron and never tagged, the next scan offers a
  "reason for your earlier departure?" screen before checking the employee in.
  Picking a reason tags that segment and creates the draft leave; picking the
  default just checks in.

## Interactions with core Attendances

- **Automatic Check Out** (`res.company.auto_check_out`): closes forgotten,
  still-open attendances via cron with `out_mode='auto_check_out'`. It bypasses
  the kiosk, so it never asks a reason or creates a leave by itself — but the
  kiosk *recognizes* such a segment on the next scan and lets the employee log
  the reason then (the leave duration is approximate and finalized by HR, since
  the real departure time is unknown).
- **Absence Management** (`res.company.absence_management`): turns unjustified
  absences into negative overtime. A kiosk reason leave only offsets the deficit
  once **approved** (a draft does not create `resource.calendar.leaves`), so
  approve the kiosk drafts promptly if this is enabled.
- **Multi-company:** the leave is filed under the kiosk's (employee's) company.
  Approvers must have that company active in their company switcher to see it.

## Design notes

- **Additive only**: core modules are untouched. New controller routes
  (`/hr_attendance/kiosk_identify`, `/hr_attendance/kiosk_action`) implement an
  identify-then-confirm flow; the original routes stay for compatibility.
- The generated leave is kept in `state='confirm'` on purpose: no
  `resource.calendar.leaves` row is created yet (no clash with the attendance
  just recorded) and the normal approval activity reaches the Time Off
  approvers.
- `hr.leave.create()` always runs `_check_validity()`, so a reason type that
  requires an allocation the employee lacks would raise. Leave creation is
  therefore wrapped in try/except: on failure the attendance is still tagged,
  only the draft leave is skipped. **Kiosk reason types should normally be
  `requires_allocation = False` and hour-based.**
- The kiosk runs `auth='public'`; all routes are scoped by the company token
  and re-validate the PIN on the action call.

## No time off types

The module ships no `hr.leave.type` records; which types exist and what each
pays is the national modules' business. The earlier, out-of-repository version
shipped four sample types; they were removed when the module came into
l10n_cssk. A database that installed that version keeps them (they were
`noupdate` data and are not deleted on upgrade).

## Technical reference

### Models

- `hr.leave.type`: `kiosk_visible` (offer this reason at the kiosk),
  `kiosk_sequence` (button order).
- `hr.attendance`: `checkout_reason_id` (the chosen reason),
  `checkout_leave_id` (the generated draft leave).
- `hr.employee` helpers:
  - `_kiosk_create_departure_leave(leave_type, attendance)`: create the draft
    leave (check-out to day end, 1 h fallback after hours). Validation errors
    are logged and swallowed so they never block the check-out.
  - `_kiosk_close_departure_leave(check_in_dt)`: trim the draft on a same-day
    return; only `confirm` leaves in hours are touched.
  - `_kiosk_tag_auto_checkout(leave_type)`: tag the latest untagged
    `auto_check_out` segment and create its draft leave.
  - `_kiosk_day_end_float(local_dt)`: last working hour from the calendar.

### Controller routes (`auth='public'`, scoped by the kiosk company token)

- `POST /hr_attendance/kiosk_identify`: identify only, no check-in/out.
  Returns the employee info plus `will_check_out`, `auto_checkout_pending`
  (+ `auto_checkout_datetime`) and `reasons`. Re-validates the PIN for manual
  selection; a wrong PIN returns `{}`, the same as an unknown employee, so the
  route does not reveal which employee ids exist.
- `POST /hr_attendance/kiosk_action`: perform the check-in/out. On a check-out
  with a reason, tag it and create the draft leave. On a check-in, trim any
  same-day draft and, with a reason, tag a prior automatic check-out.

The core routes (`attendance_barcode_scanned`, `manual_selection`) stay; the
kiosk frontend routes through the new ones. `open_kiosk_mode` coerces the
`from_trial_mode` query string to a Boolean so the OWL prop validates in debug
mode.

### Frontend (bundle `hr_attendance.assets_public_attendance`)

- `KioskLeaveReason`: the reason screen, with wording for a live check-out and
  for an earlier automatic check-out, and an optional notice banner.
- A `patch` of `kioskAttendanceApp` adding the `reason` screen, the
  identify-then-confirm routing and the automatic check-out recognition.

## Testing

Python: `--test-tags=/hr_attendance_holidays_kiosk`.

The hoot unit tests in `static/tests` carry the tag `kiosk_reason_dd`; run them
in the browser at `/web/tests?tag=kiosk_reason_dd`. `TestKioskReasonJs` drives
them headless when Chrome and `websocket-client` are available.

## Known limitations

- A leave created entirely outside working hours computes 0 paid hours
  (`hr_holidays` derives hours from calendar overlap); HR adjusts the draft.
- The duration of a departure logged after an automatic check-out is
  approximate.
- The same-day trim runs on a kiosk check-in only; checking in from the
  backend systray does not trim the draft.
