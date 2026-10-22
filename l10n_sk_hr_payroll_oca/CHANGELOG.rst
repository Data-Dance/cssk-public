=========
Changelog
=========

18.0.2.7.0 (2026-08-08)
=======================

* **Fixed: every accrual level started a day late, and the first period was
  short.** ``hr.leave.accrual.level.start_count`` defaults to **1 day** on
  18.0 (0 on 19.0), so a level began the day AFTER the allocation and Odoo
  prorated the first period 30/31: the first month of dovolenka accrued
  1.6129 days instead of 1.66667, and the § 141 annual quotas granted 6.98
  days where the statute says 7 — which also silently refused the seventh day
  of vyšetrenie at booking, since the balance never reached it. ``start_count``
  is now pinned to 0 on all ten levels. Found by porting the Enterprise
  modules to 18.0; 19.0 was never affected.
* **Fixed: the statutory leave data was frozen.** The accrual-plan and
  leave-option data files shipped ``noupdate="1"``, so no correction to them
  — including the one above — ever reached a database that had already
  installed the module. The flag is gone and a pre-migration clears it on
  ``ir.model.data``, which is written at creation and never refreshed
  otherwise. Ported from 19.0.
* The accrual test asserted ``>1 and <=20`` days for a full year, which the
  shortfall passed comfortably. It now pins the first month to exactly 1/12.

18.0.2.6.0 (2026-08-07)
=======================

Backported from 19.0. Three bugs and one family of features.

* **Fixed: an unconfirmed payslip fed the priemerný zárobok.** The search
  counted the engine's ``verify`` (Waiting) state — computed but not confirmed
  — so a half-finished month moved every náhrada in the next quarter. § 134
  counts the wage *zúčtovaná* in the determining period. The existing test
  could not have caught it: the fixture made the seeded quarter and the
  fallback produce the same 2000/176, so it passed even with the state filter
  set to ``cancel``, which selects nothing. The seed now runs at a different
  wage and a new test pins the property directly.
* **Fixed: the basic wage was prorated by DAYS while every náhrada pays by
  HOURS.** They agree only when every working day is the same length; on a
  40-hour week that is not 8+8+8+8+8 one absent 10-hour day left GROSS above
  the full wage for a reason that must leave it untouched.
* **Fixed: the employer meal contribution rounded to a third decimal.** 55 %
  of the stravné is 5.115, which a payslip line cannot hold. Rounded UP to the
  cent now, the only direction that cannot fall below the § 152 minimum.
* **Added § 142 prekážky na strane zamestnávateľa**: prestoj, poveternostné
  vplyvy, iné prekážky and vážne prevádzkové dôvody, each with its own code
  and dated percentage (100 / 50 / 100 / 60). Previously every one of them had
  to be recorded as the § 141 obstacle, which pays the full priemerný zárobok.
* **Added § 166 materská / rodičovská / otcovská**, §§ 136-138 general-interest
  absences, § 140 study leave (paid and unpaid) and karanténa. All ride
  existing codes and need no money rule.
* Backported five contract fields 18.0 was missing: ``l10n_sk_income_regular``
  (a stored editable compute defaulting from the agreement kind),
  ``l10n_sk_agreement_hours_warning`` (§§ 226 / 227 / 228a ceilings),
  ``l10n_sk_hourly_wage``, ``l10n_sk_guarantee_exempt`` and
  ``l10n_sk_health_exempt``. Several backports depended on them — the RLFO
  registration code in particular.
* The BASIC rule now reads its absence-code list from
  ``hr.payslip.l10n_sk_absence_codes()`` instead of keeping a second copy.

18.0.2.5.3 (2026-07-07)
=======================

* Corrected the dovolenka carryover validity to **364 days** (was 12 months) for
  a clean steady-state one-year forfeit. With a 12-month window the carried-days
  expiry lands on 1 January and collides with the next 1 January carryover;
  Odoo's single expiry-tracking field is then overwritten and forfeiture drifts
  to a two-year rhythm (the balance retains ~two years' worth from the second
  cohort on). 364 days makes the window close ~31 December, just before the next
  carryover, so every cycle forfeits exactly one year (matching §113: carried
  leave taken by the end of the following year). Extended the forfeiture test to
  four consecutive 1-January carryovers, asserting the year-end balance returns
  to ~one year's entitlement each cycle and the expiration date is end-of-December.

18.0.2.5.2 (2026-07-07)
=======================

* Added the Slovak §113 one-year carryover forfeiture window to the annual-leave
  (dovolenka) accrual plans. Unused dovolenka carries over into the following
  year, but if it is still unused a year later it is forfeited (practical policy
  default under §113 Zákonníka práce). Implemented on the holiday accrual
  *levels* (the 20/25/40-day monthly plans in
  ``data/hr_leave_accrual_plan_data.xml`` and the archived year-start plans in
  ``data/hr_leave_options_data.xml``) by setting ``accrual_validity`` = 12
  ``month``. Odoo counts validity FROM the 1 January carryover date, so days
  carried over on 1 Jan of year R expire on 1 Jan of year R+1 (one full year).
  The OČR (ošetrovné) and paid work-obstacle limit plans are annual caps
  (``action_with_unused_accruals='lost'``) and are deliberately left unchanged.
  New multi-year forfeiture test in ``tests/test_sk_dovolenka_accrual.py``.

18.0.2.5.1 (2026-07-07)
=======================

* Made the leave accrual-plan names translatable. Core ships
  ``hr.leave.accrual.plan.name`` as a plain, non-translatable ``Char``; a small
  model override (``models/hr_leave_accrual_plan.py``) redefines it as
  ``translate=True`` (same low-risk core-field override already used for
  ``hr.leave.type.country_id``). The shipped statutory dovolenka / OČR /
  work-obstacle plan names now carry a clean English source plus a Slovak
  (``sk``) translation in ``i18n/sk.po``; regenerated ``i18n/<module>.pot``.

18.0.2.5.0 (2026-07-07)
=======================

* Country-scoped the payroll and time-off configuration, like the accounting
  localization: ``hr.payroll.structure`` gains a ``country_id`` (and its
  ``company_id`` is relaxed to optional so a structure can be country-global);
  the shipped salary structure is set to country SK with no company, and every
  SK leave type (``hr.leave.type.country_id`` made settable on 18.0) carries
  country SK. Global record rules now filter the salary-structure list, the
  time-off configuration and the ``struct_id`` selection to the country of the
  user's active company, so an SK company only sees SK (and country-global)
  config. Accrual plans have no ``country_id`` in core and are scoped
  indirectly through their (country-scoped) leave type.

18.0.2.4.1 (2026-07-06)
=======================

* i18n pass: normalized all user-facing source strings to clean English (field labels, help tooltips, selection options, salary-rule / leave-type / accrual-plan / rule-parameter data names, view group labels), removing mixed-language parentheticals while keeping genuine token abbreviations (NČZD, ZŤP, DoVP, DoPČ, OOP, DVZ, PN, OČR, DDS). Added ``i18n/<module>.pot`` and a complete Slovak ``i18n/sk.po``.

18.0.2.4.0 (2026-07-06)
=======================

* Added ``data/hr_leave_options_data.xml`` with optional/alternative leave
  configuration. (a) ARCHIVED (``active=False``) "full entitlement at start of
  year" dovolenka accrual plans that grant the whole 20/25/40-day annual
  entitlement on 1 January (``frequency='yearly'``, ``accrued_gain_time='start'``)
  as an alternative to the default monthly 1/12 plans. (b) ACTIVE statutory
  day-cap accrual plans: OČR krátkodobé ošetrovné 14 dní/rok (zák. č. 461/2003
  Z. z. §42; ošetrovné is a Sociálna poisťovňa benefit, employer only records the
  absence — 90-day dlhodobé limit documented in the file header) and paid
  prekážky v práci §141 Zákonníka práce (vyšetrenie/ošetrenie 7 dní/rok,
  sprevádzanie rodinného príslušníka 7 dní/rok, sprevádzanie ZŤP dieťaťa 10
  dní/rok). Full per-reason §141/§138 table (svadba, úmrtie, sťahovanie,
  narodenie dieťaťa, darovanie krvi) documented in the data-file header. Sources
  confirmed for 2025/2026.

18.0.2.3.0 (2026-07-06)
=======================

* Statutory annual-leave (dovolenka) accrual plans as install data, attached to
  the SK holiday leave type (``l10n_sk_leave_type_dovolenka`` via
  ``time_off_type_id``) and modelled in DAYS (Zákonník práce, zák. č. 311/2001
  Z. z., §100–§117): "Základná dovolenka 4 týždne (20 dní)" (§103 ods. 1),
  "Dovolenka 5 týždňov (25 dní)" pre zamestnanca, ktorý do konca roka dovŕši 33
  rokov alebo sa trvale stará o dieťa (§103 ods. 2), a "Dovolenka 8 týždňov
  (40 dní)" pre pedagogických/akademických/výskumných zamestnancov (§103 ods. 3).
  Each plan accrues 1/12 of the annual entitlement per whole calendar month
  (``frequency='monthly'``, ``added_value=annual/12``, ``added_value_type='day'``)
  so a full year yields 20/25/40 days and a partial year the pomerná časť (§101);
  ``maximum_leave_yearly`` caps each year at the statutory figure and unused days
  carry over (§113). Proration assumption documented in the data file. The §105
  "dovolenka za odpracované dni" (1/12 per 21 worked days when <60 days worked)
  and the 33+/child eligibility (§103 ods. 2) are NOT derivable from payroll data
  — the plan must be assigned per employee manually. New demo: a start-of-year
  20-day allocation on the demo holiday type.

18.0.2.2.0 (2026-07-05)
=======================

* Annual tax reconciliation (ročné zúčtovanie preddavkov na daň, §38 zákona
  č. 595/2003 Z. z.): new ``l10n.sk.tax.reconciliation`` model per (employee,
  year) that gathers the year's Σ tax base / Σ advances / Σ child bonus from the
  monthly payslips, recomputes the annual tax with the annual NČZD (taper),
  annual bands, NČZD na manželku, DDS (III. pilier, capped 180 €) and the annual
  child-bonus entitlement, and yields a preplatok/nedoplatok. The result is
  posted onto the reconciliation-month payslip via the input-driven
  ``ANNUAL_TAX_SETTLEMENT`` rule (positive → net, negative → nedoplatok);
  standard monthly payslips are unchanged. New dated parameters
  ``l10n_sk_nczd_annual``, ``l10n_sk_income_tax_bands_annual``,
  ``l10n_sk_dds_annual_cap`` (2025 & 2026, with sources). The annual health-
  insurance reconciliation stays out of scope (insurer-side, §19 zák. 580/2004).

18.0.2.1.0 (2026-07-05)
=======================

* Absence → payroll integration: new ``hr.leave.type.l10n_sk_payroll_code``
  (DOVOLENKA / PN / OCR / NEPLATENE / OBSTACLE) and starter leave types; the
  leave-day computation keys worked-day lines on it, so any absence prorates
  BASIC.
* Average earnings (priemerný hodinový zárobok, §134): prior-calendar-quarter
  gross ÷ worked hours, with the probable-earnings fallback and the minimum
  hourly-wage floor (dated ``l10n_sk_min_hourly_wage``).
* Holiday and paid-obstacle náhrada (``DOVOLENKA_NAHRADA`` / ``OBSTACLE_NAHRADA``)
  at priemerný zárobok, insurable + taxable (no net proration cut on holiday).
* Sickness compensation now derives its sick days from the PN leave (manual
  ``PN_DAYS`` kept as fallback).

18.0.2.0.2 (2026-07-05)
=======================

* Partial-month proration of the basic wage (mid-month hire/leaver).
* Wage garnishment (exekučné zrážky) with the non-seizable amount, input-driven
  (ordinary 1/3 / priority 2/3), computed on the net wage; new
  ``l10n_sk_garnishment_dependents`` field and dated parameters.
* Sickness compensation (náhrada príjmu pri PN), input-driven employer-paid sick
  pay (days 1–3 at 25%, days 4–10/14 at 55% of the capped DVZ).

18.0.2.0.1 (2026-07-04)
=======================

* Added the health-insurance OOP (odvodová odpočítateľná položka na zdravotné
  poistenie): max 380 €/mo, phased out to 0 at 570 €, reducing only the
  employee's health assessment base for a regular employment relationship, when
  claimed (new ``l10n_sk_health_oop_claim`` field, dated parameters).
* Implemented the agreements (dohody) DoVP / DoPČ contribution treatment: DoVP is
  charged as irregular income (no sickness / unemployment / short-time-work
  financing), DoPČ as regular income; added the pension odvodová odpočítateľná
  položka (200 €/mo) reducing the old-age, disability and reserve-fund base for
  eligible pensioners/students.

18.0.2.0.0 (2026-07-04)
=======================

* Income tax is computed on the correct tax base
  (gross − employee social − employee health − NČZD) instead of on the raw
  gross.
* Non-taxable part per taxpayer (NČZD) applied, gated by the signed taxpayer's
  declaration, with the high-income taper.
* Health insurance rates and the maximum social assessment base moved to dated
  rule parameters with current values (2025 and 2026).
* Added the child tax bonus (daňový bonus na dieťa) with per-child amounts,
  the percentage-of-tax-base caps and the high-income taper.
* Added ZŤP (disability) handling with the halved health rate and the health
  minimum-base top-up (doplatok).
* Progressive income-tax band table with dated values.
* Meal allowance reworked into meal-voucher and financial-contribution options
  with the statutory minimum employer contribution.
* All statutory rates and ceilings parameterised as dated values.

18.0.1.0.0
==========

* Initial Slovak payroll structure, categories and salary rules on the
  ``payroll`` engine.
