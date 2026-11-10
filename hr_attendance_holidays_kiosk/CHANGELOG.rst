=========
Changelog
=========

[19.0.1.0.0] — 2026-11-10
-------------------------

Added
~~~~~

- First release in this repository. The attendance kiosk asks for a reason
  when an employee checks out; a reason creates a draft time off from the
  check-out to the end of the working day, shortened when the employee returns
  the same day. A segment closed by the automatic check-out can be given its
  reason on the next scan.
- A *Show in Attendance Kiosk* flag on time off types and a reorderable
  *Kiosk Reasons* list. The module ships no time off types: those belong to
  the national modules. The four sample types of the earlier, out-of-repository
  version are gone.
- Licensed AGPL-3 (previously LGPL-3 outside this repository).
