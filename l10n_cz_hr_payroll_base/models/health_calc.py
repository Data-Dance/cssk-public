# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Czech employee health-insurance premium — deliberately free of Odoo imports.

Shared by both payroll engines so they cannot drift.

* § 2 zákona č. 592/1992 Sb.: the premium is 13,5 % of the vyměřovací základ
  and "se zaokrouhluje na celé koruny směrem nahoru" — per employee, since the
  amount remitted to an insurer is the sum of the employees' rounded premiums.
* § 9 odst. 2 zákona č. 48/1997 Sb.: "Pojistné za zaměstnance hradí z jedné
  třetiny zaměstnanec, ze dvou třetin zaměstnavatel." The employee's third of
  the rounded premium is rounded up; the employer pays the rest.
* § 3 odst. 4, 6 and 10 zákona č. 592/1992 Sb.: the premium is due at least
  from the minimální vyměřovací základ (the minimum wage); the employee tops
  up 13,5 % of the shortfall, unless the base is lower "z důvodů překážek na
  straně organizace", in which case the employer pays the difference.

The minimum base handed in must already be prorated (§ 3 odst. 9) and zero
where it does not apply (§ 3 odst. 8, state-insured persons, agreements).
"""

import math


def _ceil_crown(value):
    """Round *value* up to whole crowns, immune to IEEE-754 noise."""
    if value <= 0.0:
        return 0.0
    return float(math.ceil(round(value, 6)))


def health_premiums(base, min_base, rate_ee, rate_er, employer_pays_topup=False):
    """Return ``(employee, employer)`` health premium in whole crowns.

    *base* is the actual vyměřovací základ, *min_base* the (prorated) minimum
    base or 0 where none applies, *rate_ee*/*rate_er* the percentage shares
    (4,5 / 9). *employer_pays_topup* moves the minimum-base top-up to the
    employer (§ 3 odst. 10, last sentence).
    """
    rate_total = rate_ee + rate_er
    if rate_total <= 0.0:
        return 0.0, 0.0
    base = max(base, 0.0)
    premium = _ceil_crown(base * rate_total / 100.0)
    employee = _ceil_crown(premium * rate_ee / rate_total)
    employer = premium - employee
    if min_base > base:
        topup = _ceil_crown(min_base * rate_total / 100.0) - premium
        if employer_pays_topup:
            employer += topup
        else:
            employee += topup
    return employee, employer
