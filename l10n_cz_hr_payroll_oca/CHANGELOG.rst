=========
Changelog
=========

18.0.1.6.0 (2026-08-08)
=======================

* **Fixed: every accrual level started a day late.**
  ``hr.leave.accrual.level.start_count`` defaults to 1 day on 18.0 (0 on
  19.0), so the level began the day after the allocation and Odoo prorated
  the first period 30/31. Pinned to 0 on all four levels. 19.0 was never
  affected.

18.0.1.5.0 (2026-08-08)
=======================

Backported from 19.0.

* **Added §§ 207-209 překážky na straně zaměstnavatele**: prostoj (nejméně
  80 %), povětrnostní vlivy (nejméně 60 %), jiné překážky (100 %) and částečná
  nezaměstnanost (nejméně 60 %). Each has its own worked-day code and dated
  percentage, and one ``PREKAZKANAHRADA`` rule sums them. Previously every one
  of these had to be recorded as the § 199 paid obstacle, which pays the FULL
  průměrný výdělek — overpaying a prostoj by a fifth and a short-time month by
  two fifths.
* **Added §§ 195-196 mateřská / rodičovská / otcovská**, §§ 201-203
  general-interest absences, § 232 study leave (paid and unpaid) and
  karanténa. All ride existing codes and need no money rule; the employer pays
  nothing for the family leaves, which are dávky of ČSSZ.

18.0.1.4.3 (2026-07-07)
=======================

* Corrected the dovolená carryover validity to 364 days for a clean steady-state
  one-year forfeit. The previous 12-month validity expired on the same 1 Jan as
  the carryover, and Odoo's expiry recompute then looked one carryover too far
  ahead, drifting into a two-year retention from the second cohort on. 364 days
  lands the expiry on ~31 Dec, just before the 1 Jan carryover, so leave earned
  in year N carries into N+1 and lapses at the end of N+1 -- every cycle. The
  multi-year test now drives five successive year-end/1 Jan cycles and asserts a
  clean one-year forfeiture each time (steady-state balance ~20 days, never two
  years) with the expiry always at end of December.

18.0.1.4.2 (2026-07-07)
=======================

* Added the § 218 zákoníku práce one-year carryover window to the dovolená
  accrual plans. Unused annual leave carries into the following calendar year,
  but leave still untaken a year after it rolled over is forfeited. On the
  holiday accrual levels (the 4-week and 5-week per-worked-week plans and the
  archived "full entitlement on 1 Jan" variants) this is now expressed with
  ``accrual_validity`` = 12 months, which Odoo counts from the 1 Jan carryover
  date, so leave earned in year N rolls over on 1 Jan N+1 and expires on
  1 Jan N+2. A new multi-year test (``tests/test_holiday_carryover.py``) drives
  the accrual engine across three successive 1 Jan carryovers and asserts the
  forfeiture of the untaken carried days.

18.0.1.4.1 (2026-07-07)
=======================

* Made the leave accrual-plan ``name`` translatable. Core Odoo defines
  ``hr.leave.accrual.plan.name`` as a non-translatable ``Char``; a small model
  inherit (``models/hr_leave_accrual_plan.py``) redefines it with
  ``translate=True`` so the statutory dovolená plans ship an English source term
  and a Czech (cs) translation, like every other user-facing name. Normalized
  the four plan names to clean English (e.g. ``Statutory annual leave — 4 weeks
  (160 h/year)``, ``Annual leave — 4 weeks, full entitlement on 1 Jan (160 h)``)
  and added their Czech translations in ``i18n/cs.po``.

18.0.1.4.0 (2026-07-07)
=======================

* Country-scoped the payroll and time-off configuration, like the accounting
  localization: ``hr.payroll.structure`` gains a ``country_id`` (and its
  ``company_id`` is relaxed to optional so a structure can be country-global);
  the shipped salary structure is set to country CZ with no company, and every
  CZ leave type (``hr.leave.type.country_id`` made settable on 18.0) carries
  country CZ. Global record rules now filter the salary-structure list, the
  time-off configuration and the ``struct_id`` selection to the country of the
  user's active company, so a CZ company only sees CZ (and country-global)
  config. Accrual plans have no ``country_id`` in core and are scoped
  indirectly through their (country-scoped) leave type.

18.0.1.3.2 (2026-07-06)
=======================

* English source strings + Czech translation: all user-facing source strings
  (field labels, help tooltips, selection options, salary rules / categories,
  rule parameters, leave and accrual-plan record names) rewritten to clean
  English with no mixed-language content; shipped ``i18n/<module>.pot`` and a
  complete Czech ``i18n/cs.po``.

18.0.1.3.1 (2026-07-06)
=======================

* Optional/alternative statutory-limit leave configuration
  (``data/hr_leave_options_data.xml``):

  * Two ARCHIVED (``active=False``) "full entitlement at start of year" dovolená
    accrual plans as an alternative to the per-worked-week accrual —
    ``accrual_plan_cz_holiday_4w_yearstart`` (160 h) / ``_5w_yearstart`` (200 h):
    the whole year's entitlement is granted in a single yearly milestone on
    1 January (frequency yearly, accrued_gain_time=start, not worked-time based).
    Un-archive to use.
  * OČR / ošetřovné statutory day-limit leave types (active): krátkodobé
    ošetřovné 9 dní (16 for a lone parent, zák. č. 187/2006 Sb. § 39) and
    dlouhodobé ošetřovné 90 dní (§ 41a–41c). OČR is a ČSSZ nemocenské benefit,
    not employer pay; ``requires_allocation`` lets a company cap recorded OČR.
  * Paid-obstacle day-limit leave type (active): doprovod k lékaři max 1 den
    (NV č. 590/2006 Sb.); per-reason limits (svatba, pohřeb, stěhování, …) are
    documented in the file header.

18.0.1.3.0 (2026-07-06)
=======================

* Statutory Czech annual-leave (dovolená) accrual plans, attached to the
  CZ holiday time-off type. Two ``hr.leave.accrual.plan`` records model the
  hours-based entitlement in force since 1.1.2021 (zákoník práce § 212–§ 213):
  ``accrual_plan_cz_holiday_4w`` (minimum výměra 4 týdny = 160 h/rok) and
  ``accrual_plan_cz_holiday_5w`` (5 týdnů = 200 h/rok). Each carries one weekly,
  worked-time-based level that accrues 1/52 of (weekly hours × výměra) per worked
  week (§ 213 odst. 4), i.e. 3.076923 h / 3.846154 h per week, with carry-over of
  unused leave (§ 218). ASSUMPTION (human-verify): the plans are calibrated for
  the standard full-time 40 h/týden; for other weekly hours an admin must scale
  ``added_value`` pro rata, since Odoo accrual cannot read the contract's weekly
  hours. Plans are generic (no time_off_type_id) so an admin assigns one when
  creating an employee allocation. A demo start-of-year allocation (20 days =
  4 týdny = 160 h) is added to the demo holiday type.

18.0.1.2.0 (2026-07-05)
=======================

* Employer social-insurance discount (sleva na pojistném na sociální pojištění,
  §7a–§7f zák. 589/1992 Sb., in force since 1.2.2023). A new
  ``l10n_cz_social_discount_category`` field (none / over55 / parent_under10 /
  carer / student / retraining / disabled / under21, mapped to the § 7a odst. 1
  reason letters a–g) drives a new ``SOCIAL_DISCOUNT`` salary rule: for an
  eligible employee with a shorter working time of 8–30 h/week (employees under
  21 are exempt from the hours band) whose monthly assessment base is within
  1.5× the average wage, the rule books −5 % of that base as an employer saving.
  It sits in its own ``SOCIAL_DISCOUNT`` category so the gross SOCIALER/
  SOCIALERTOT premium is unchanged while ``EMPLOYERCOST`` is reduced; full-time
  employees with no category are unaffected. New dated parameters:
  ``l10n_cz_social_disc_rate`` (5 %), ``l10n_cz_social_disc_base_mult`` (1.5),
  ``l10n_cz_social_disc_hours_min`` (8), ``l10n_cz_social_disc_hours_max`` (30),
  ``l10n_cz_social_disc_hours_month_max`` (138).

18.0.1.1.0 (2026-07-05)
=======================

* Annual tax reconciliation (roční zúčtování záloh na daň z příjmů ze závislé
  činnosti, §38ch/§38ča ZDP). A new ``hr.payroll.cz.annual.tax.recon`` record per
  (employee, year) aggregates the year's done payslips (Σ tax base, Σ withheld
  advance, Σ credit, Σ child benefit / bonus) and computes the annual tax base
  (Σ gross minus the §15 non-taxable parts, rounded down to whole 100 Kč), the
  annual tax (15 % / 23 % above 36× průměrná mzda: 1 676 052 for 2025, 1 762 812
  for 2026), the §35ba credits (sleva na poplatníka 30 840 in full, manžel/ka,
  ZTP/P, invalidita) and the §35c child benefit / annual daňový bonus, then the
  přeplatek (refund) and the doplatek na daňovém bonusu. The settlement is posted
  onto a payslip (usually March) via the new input-driven ANNUAL_TAX_SETTLEMENT
  rule (ALW, lifts net pay); standard monthly payslips are unchanged.

18.0.1.0.4 (2026-07-05)
=======================

* Absence → payroll integration and a real average-earnings mechanism. CZ
  absences (holiday / sickness / OČR / unpaid / paid-obstacle) are recorded as
  leaves mapped to stable payroll codes (via ``l10n_cz_payroll_code`` on the
  leave type and a ``_compute_leave_days`` override), so every absence prorates
  BASIC down. Holiday and paid-obstacle time is compensated at the průměrný
  výdělek (§351–362 zákoníku práce), computed from the previous calendar quarter
  and floored at the minimum-wage hourly rate (manual field kept as an
  override), into the insurable + taxable GROSS. Sickness compensation is now
  driven from the sickness leave (SICK_HOURS input kept as a fallback). Unpaid
  leave triggers the health minimum-base top-up. Existing standard / dohody /
  garnishment / sickness-input behaviour and a full worked month are unchanged.

18.0.1.0.3 (2026-07-05)
=======================

* P3 payroll features: worked-days proration of the basic wage (BASIC prorated
  by worked/scheduled time); wage garnishment (exekuční srážky) with the 2026
  nezabavitelná částka and the priority/non-priority thirds split; sickness
  compensation (náhrada mzdy) for the first 14 days with the redukční hranice.
  The garnishment and sickness rules are input-driven, so existing standard /
  dohody payslips are unchanged.

18.0.1.0.2 (2026-07-05)
=======================

* Fixed the NET salary rule missing its ``code`` (the net line was created
  without a code, so it could not be read back). Found via runtime testing.
* Removed the ``country_id`` field from the salary-rule categories: the payroll
  engine's ``hr.salary.rule.category`` has no such field. Found via runtime
  testing.

18.0.1.0.1 (2026-07-04)
=======================

* Agreements (dohody): DPP and DPČ insurance thresholds and taxation. Below the
  rozhodný příjem (notified DPP 25 % of the average wage; non-notified DPP / DPČ
  the general threshold) no social or health insurance is charged and, without a
  signed taxpayer declaration, the income is taxed by the 15 % final withholding
  tax (srážková daň) instead of the advance. Standard employment is unchanged.

18.0.1.0.0 (2026-07-04)
=======================

* Initial release: Czech monthly payroll for standard employment on the
  ``payroll`` engine.
* Social insurance (employee 7.1 % / employer 24.8 %) with the 48× annual
  assessment-base cap tracked year-to-date.
* Health insurance (4.5 % / 9 %) with the minimum-base top-up and the
  state-insured skip.
* Income-tax advance (15 % / 23 %) on the gross tax base, with the monthly
  23 % threshold and the round-up-to-100 base.
* Tax credits (sleva na poplatníka, ZTP/P, invalidita) and the child tax
  benefit / daňový bonus by tier.
* Meal allowance (stravenkový paušál) tax-exempt limit.
* All statutory rates and thresholds parameterised as dated values for 2025
  and 2026, via a lightweight ``hr.rule.parameter`` mechanism.
