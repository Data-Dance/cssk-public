=========
Changelog
=========

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- 19.0.2.0.0 (the two-step process, access rules, advance and printed forms)
  is not on 18.0, which is at 18.0.1.1.0. The port also needs
  ``hr_expense_advance_clearing`` on 18.0: OCA has it there, built on
  ``hr.expense.sheet``, so the clearing calls differ from the 19.0 module
  vendored here.

[19.0.2.0.0] — 2026-11-10
-------------------------

Added
~~~~~

- Two-step process, as zákon 283/2002 Z. z. has it: the order is submitted
  and approved before the trip (§ 3), and the settlement is submitted and
  approved after it (§ 36). States Draft, To Approve, Approved, Settlement to
  Approve, Settled, Refused, Cancelled; the planned times and who approved and
  settled, and when, are kept.
- The approver is resolved like the expense approver: expense approver,
  department manager, then manager. Only an expense officer can change it.
  Activities for the approver, and for the employee with the 10-working-day
  deadline of § 36 ods. 7; the approver's deadline of ods. 8 on the
  settlement.
- Advance: approving the order creates an approved employee advance
  (``hr_expense_advance_clearing``, account 335000 on the Slovak chart). The
  settlement clears it, and the unused part is returned with Return Advance.
- Other costs (tickets, accommodation, parking) as expenses on the order, with
  their receipts, approved with the settlement.
- Printed Cestovný príkaz and Vyúčtovanie pracovnej cesty.
- Search filters (my trips, to approve, settlement overdue, advance to clear),
  a kanban view, and menus To Approve and All Travel Orders.
- Meal allowance of oznámenie č. 255/2026 Z. z. from 1. 12. 2026: 9.80, 14.60
  and 21.70 €.

Changed
~~~~~~~

- Depends on ``hr_expense_advance_clearing``.
- Settling creates one expense for the allowances instead of one for the
  amount due after the advance; the advance is cleared in accounting.

Security
~~~~~~~~

- Record rules: employees see their own orders, approvers their team's,
  expense officers all. Before, every internal user could read and change
  every order in the company.
- Every step checks its rights on the server, not only in the view. Nobody
  approves their own trip, and the state and approval fields cannot be
  written directly.
- An order and its days are locked once submitted. After approval only the
  employee, or an expense officer, enters the trip as it went. No costs can
  be added once the settlement is submitted.

[19.0.1.1.0] — 2026-11-10
-------------------------

Added
~~~~~

- Foreign travel orders: border times, countries visited, the domestic
  allowance for the hours in Slovakia (§ 16), the foreign allowance of the
  decisive country by the bands of § 13 ods. 4 and 5 with meal cuts of § 13
  ods. 7, optional pocket money (§ 14), and conversion at the rate of the first
  day of the month the trip began (§ 36 ods. 6).
- The base rates of opatrenie MF SR č. 401/2012 Z. z. for 193 countries and the
  road-transport rates of opatrenie č. 9/2026 Z. z. from 30. 1. 2026.

[19.0.1.0.1] — 2026-11-09
-------------------------

Fixed
~~~~~

- The shipped rates start on 1. 1. 2026: the kilometre rate of 340/2025 does
  not apply earlier. Meals follow 280/2025.

[19.0.1.0.0] — 2026-11-09
-------------------------

Added
~~~~~

- Vehicle logbook, domestic travel orders and settlement through Expenses.
