=========
Changelog
=========

[18.0.1.2.0] — 2026-11-10
-------------------------

Changed
~~~~~~~

- Ported from 19.0.2.1.0: each free meal has its own "abroad" tick instead
  of one per day, so each meal cuts the part of the day where it was
  provided (§ 5 ods. 6, § 13 ods. 7, § 16 ods. 1), each only down to zero.
  The migration copies the old per-day switch to all three meals; amounts
  do not change.

Added
~~~~~

- Ported from 19.0.2.1.0: fuel lines (§ 15) with kilometres, unit price and
  currency per part of the trip, converted at the first-of-month rate of
  § 36 ods. 6, with a warning when they do not add up to the trip.

[18.0.1.1.0] — 2026-11-10
-------------------------

Added
~~~~~

- Ported from 19.0.1.1.0: vehicle logbook, domestic and foreign travel
  orders and settlement through Expenses. Domestic meals, kilometre and
  fuel reimbursement (§§ 5, 7 zákona 283/2002 Z. z.) with the rates from
  1. 1. 2026; foreign trips with border times, countries visited, the
  domestic allowance for the hours in Slovakia (§ 16), the foreign
  allowance of the decisive country (§ 13 ods. 4, 5, 7), optional pocket
  money (§ 14) and conversion at the rate of the first day of the month
  the trip began (§ 36 ods. 6). Ships the base rates of opatrenie MF SR
  č. 401/2012 Z. z. for 193 countries and the road-transport rates of
  č. 9/2026 Z. z. from 30. 1. 2026.
