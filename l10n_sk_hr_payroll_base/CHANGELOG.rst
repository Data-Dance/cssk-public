=========
Changelog
=========

18.0.1.1.3 (2026-11-16)
-----------------------

* **Fixed: a student on a DoBPŠ is no longer charged sickness or unemployment insurance** (nor the short-time work contribution, nor offered sickness compensation), even with a regular monthly income: § 4 ods. 1 písm. a) zákona 461/2003 takes the DoBPŠ out of the definition of a zamestnanec for those funds, and with a regular income the student is pension-insured only (§ 4 ods. 2 písm. b) bod 1). Read by the Enterprise engine; the OCA engine has no DoBPŠ form on 18.0.
* Pensioners on a DoVP/DoPČ (§ 4 ods. 1 písm. b)) are still charged, because the contract records no pension status.
* Port of 19.0.1.0.1 (19.0 ``ffd67cd0c``).

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
