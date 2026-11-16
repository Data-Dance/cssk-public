=========
Changelog
=========

18.0.1.1.2 (2026-11-16)
-----------------------

* Shared sick-pay arithmetic in ``sick_pay.py``: the daily base is cut to four decimals (§ 8 ods. 8 zákona 462/2003 Z. z.) and the compensation rounded up to the cent (§ 10 ods. 2), in decimal arithmetic. Port of 19.0.1.2.1.

18.0.1.1.1 (2026-11-16)
-----------------------

* **Fixed: the part-month employee cap floors the daily base first** (§ 138 ods. 13 zákona 461/2003 Z. z., last sentence). The monthly maximum is divided by the days of the month, cut to the cent, and only then multiplied by the insured days: 540.77 × 16 = 8652.32 for a hire on 16 January 2026, not 8652.38. A full month keeps the whole maximum; the employer's cap is unchanged. Port of 19.0.1.2.2.

18.0.1.1.0 (2026-11-09)
-----------------------

* Helpers for the part-month cap and the calendar-day sick-pay split.

19.0.1.0.0 (2026-08-03)
-----------------------

* Initial release.
* ``applicability`` — one table stating which contributions and entitlements
  apply to which of the four Slovak employment forms, and under which income
  regularity. Odoo-free, so it reads and diffs as the statement of law it is.
* ``hr.version.l10n_sk_applies(concept)`` — reachable from a salary-rule
  condition on either engine, since both hand the version to every rule.
* An unknown concept raises. Returning a default would let a typo look like a
  legal answer, and every caller is deciding whether to charge or pay someone.
