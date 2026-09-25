=========
Changelog
=========

19.0.1.18.0 (2026-08-07)
========================

* Added the remaining **prekážky z dôvodu všeobecného záujmu**: výkon verejnej
  funkcie (§ 136) and občianska povinnosť (§ 137), alongside the darovanie
  krvi (§ 138) added earlier. All are paid at priemerný zárobok, so they carry
  the ``OBSTACLE`` code and need no money rule; the separate types exist
  because the legal reason differs and an employer has to record which it was.
* Vojenské cvičenie is deliberately absent — who pays and who reimburses the
  employer is question 10 in the practitioner document.

19.0.1.17.0 (2026-08-07)
========================

* **Four more statutory absences, none of which needed a money rule.** Each
  carries an EXISTING payroll code, so the payslip treats it exactly as the
  bucket it belongs to and the separate type exists so HR can record and
  report what actually happened:

    - darovanie krvi (§ 138) — paid at priemerný zárobok (``OBSTACLE``)
    - vzdelávanie, paid and unpaid variants (§ 140) — ``OBSTACLE`` /
      ``NEPLATENE``
    - karanténa — paid as a sickness (``PN``), driving the same employer
      sick-pay náhrada

  § 140 ships BOTH variants deliberately: the statute leaves paid study leave
  to the employer, so which applies is a decision rather than something to
  encode as automatic. Karanténa carries the PN code rather than one of its
  own because the money is identical and a separate code would only take it
  out of the sick-pay rule.

19.0.1.16.0 (2026-08-07)
========================

* **Fixed: the employer meal contribution differed by ten cents between the
  engines.** 55 % of the 2026 stravné is exactly 5.115 a day — a third decimal
  a payslip line cannot hold. Both engines store the amount rounded to 5.12,
  but they derive the line TOTAL differently: the OCA engine from the rounded
  amount (20 x 5.12 = 102.40), Enterprise from the unrounded value (102.30).
  The per-day contribution is now rounded UP to the cent in both rules, as the
  surcharge kernel already does for statutory floors — § 152 sets a MINIMUM,
  so up is the only direction that cannot breach it. Both engines now report
  102.40 and a NET of 1583.59.

19.0.1.15.0 (2026-08-06)
========================

* **Fixed: an unconfirmed payslip fed the priemerný zárobok.** The search
  counted the OCA engine's verify (Waiting) state — computed but not
  confirmed — so a half-finished month moved every náhrada in the next
  quarter. §134 counts the wage *zúčtovaná* in the determining period, and the
  Czech side had always filtered on done alone. Found by the engine-seam
  audit comparing the two COUNTRIES rather than the two engines.
* The existing prior-quarter test could not have caught it: the fixture made
  both branches produce 2000/176, so it passed even with the state filter set
  to cancel, which selects nothing. The seed is now paid at a different
  wage so the seeded quarter and the fallback are distinguishable, and a new
  test pins that an unconfirmed seed falls back rather than counting.

19.0.1.14.0 (2026-08-06)
========================

* **Maternity, parental and paternity leave can now be recorded.** § 166
  absences had no leave type at all, so there was no way to put one on a
  payslip. Three new types with their own payroll codes (``MATERSKA`` /
  ``RODICOVSKA`` / ``OTCOVSKA``). The employer pays NOTHING — materské,
  rodičovský príspevok and otcovské are dávky of the Sociálna poisťovňa — so
  they behave like OČR: the wage prorates down and no náhrada is added.
* They are deliberately NOT folded into the OČR code. The SP filings have to
  tell them apart: rodičovská drives a prerušenie povinného poistenia on the
  RLFO, and the vylúčené doby on the ELDP differ by reason. Neither is derived
  yet — see the ROADMAP — but the absence they will be derived FROM now exists.

19.0.1.13.0 (2026-08-05)
========================

* **Fixed: the basic wage was prorated by DAYS while every náhrada pays by
  HOURS.** They only agree when every working day is the same length. On a
  40-hour week that is not 8+8+8+8+8 — a short Friday, the ordinary kratší
  piatok schedule — they do not: one absent 10-hour day cut 1/19.5 of the
  wage while the náhrada paid 10 hours, leaving GROSS **11.08 EUR ABOVE the
  full wage** for a reason that must leave it untouched. BASIC now prorates by
  hours, which is what the Enterprise engine has always done, so this closes
  an 11 EUR divergence between the two engines on identical input as well.
  Holiday, § 141 and § 142 náhrady were all affected; a uniform 8-hour
  calendar is unchanged to the cent.
* The BASIC rule now reads its absence-code list from
  ``hr.payslip.l10n_sk_absence_codes()`` instead of carrying a second copy in
  the XML. The Python constant existed but nothing read it, so adding an
  absence type in one place and not the other would silently stop prorating
  the wage for it.

19.0.1.12.0 (2026-08-05)
========================

* **Fixed: every § 142 employer-side obstacle was paid at the full priemerný
  zárobok.** There was one paid-obstacle bucket, taken from § 141 (the
  EMPLOYEE's side, where the full rate is right), so a prestoj stopped by bad
  weather — § 142 ods. 2, náhrada najmenej 50 % — was overpaid by half, and
  the § 142 ods. 4 vážne prevádzkové dôvody rate of 60 % was overpaid by
  two fifths. Each reason now has its own leave type, its own worked-day code
  and its own dated percentage:

    - ``PREKAZKA_PRESTOJ`` § 142 ods. 1 prestoj — 100 %
    - ``PREKAZKA_POCASIE`` § 142 ods. 2 nepriaznivé poveternostné vplyvy — 50 %
    - ``PREKAZKA_INE`` § 142 ods. 3 iné prekážky — 100 %
    - ``PREKAZKA_VAZNE`` § 142 ods. 4 vážne prevádzkové dôvody — 60 %

  The percentages are statutory MINIMA a collective agreement may raise, so
  they are dated ``hr.rule.parameter`` records rather than literals in a rule.
  One new rule ``PREKAZKA_NAHRADA`` sums them; it is regular wage income
  (insurable + taxable) and rolls into GROSS like the holiday náhrada. The
  generic § 141 obstacle is unchanged and still paid in full.

19.0.1.11.0 (2026-08-05)
========================

* **Fixed: the two engines disagreed on the priemerný zárobok.** When the
  §134 ods. 3 test failed — under 168 hours in the determining quarter, i.e.
  new hires, returners, anyone with a short prior period — the probable
  earnings were computed from a flat 174 monthly hours on Enterprise and from
  the period's own scheduled hours on OCA. June 2026 schedules 176, so the same
  employee got an hourly figure 1.1 % apart depending on engine, and that
  number feeds every dovolenka and paid-obstacle náhrada. Both now use the
  period's schedule, which is what "mzda, ktorú by zrejme dosiahol" asks for.
* Enterprise also counted DRAFT payslips in the determining period
  (``state != 'cancel'``) where OCA counted only confirmed ones. A draft wage
  is not zúčtovaná and must not feed the average; Enterprise now matches.
* The §134 ods. 3 threshold moved from a literal in Python to the
  ``l10n_sk_avg_earnings_min_hours`` rule parameter, read by both engines, so
  the two cannot drift apart on it again.

19.0.1.10.1 (2026-08-05)
========================

* **The statutory leave configuration is updatable again.** The Slovak leave
  types, work-entry types and accrual plans shipped with ``noupdate="1"``,
  which froze them at their install-time values — a corrected day-cap or a
  reworked plan never reached a database that had already installed the
  module. These records are legislation, not customer configuration, so the
  flag is gone, matching how the Czech modules have always shipped them.
  Note the consequence: local edits to these particular records are now
  overwritten on module update.
* Added a pre-migration that clears the stored ``ir.model.data.noupdate``
  flag. Dropping the attribute from the data files is not enough on its own —
  the column is written when the row is created and never refreshed, and
  ``_build_update_xmlids_query`` skips exactly the rows flagged as
  non-updatable, so an upgraded database would otherwise keep the frozen
  records forever. This also carries the previous version's §141 leave-type
  split onto databases installed before it.

19.0.1.10.0 (2026-08-05)
========================

* **§141 annual day-caps are now enforceable per reason.** The three capped
  paid-obstacle reasons (vyšetrenie 7 dní, sprevádzanie rodinného príslušníka
  7 dní, sprevádzanie ZŤP dieťaťa 10 dní) each get their own leave type with
  ``requires_allocation=True``, instead of all three accrual plans hanging off
  the single generic obstacle type. Odoo pools every allocation of the same
  leave type into one balance, so the previous layout enforced a single
  24-day pot and let an employee book twelve consecutive days of vyšetrenie.
  The generic ``l10n_sk_leave_type_obstacle`` deliberately keeps
  ``requires_allocation=False``: it carries the per-EVENT §141 reasons
  (svadba, úmrtie, narodenie dieťaťa, darovanie krvi §138) that have no annual
  quota, and requiring an allocation there would make a funeral day unbookable
  once an unrelated quota ran out. All four types keep the OBSTACLE payroll
  code, so payslips are unaffected. OČR is intentionally left unenforced — a
  hard 14-day block would reject a legitimate dlhodobé ošetrovné (§42 ods. 5).


19.0.1.6.0 (2026-07-27)
=======================

* **Fixed: the non-seizable base for priority claims.** ``GARNISHMENT_PRIORITY``
  was computed on the ordinary 140 % ŽM base; under § 2 ods. 2 NV 268/2006 a
  priority creditor may reach deeper and the protected base is 100 % ŽM. Every
  priority garnishment was therefore under-deducted (roughly 118 €/month at the
  2026 subsistence minimum). Added the ``l10n_sk_garnishment_priority_coeff``
  rule parameter. The § 3 unlimited-seizure threshold correctly stays keyed to
  the § 1 ods. 1 basic sum in both cases.
* Added the subsistence minimum valid from 1.7.2026 (295.22 €; basic
  non-seizable amount 413.31 €) — the parameters previously stopped at 284.13 €.
* **Wage garnishment now delegates to the garnishment register.** When
  ``l10n_cssk_hr_payroll_garnishment_base`` is installed, the ``GARNISHMENT``
  rule applies the full multi-claim waterfall across every execution order on
  file, with the correct per-claim-class base (ordinary 140 %, priority 100 %,
  maintenance of a minor 70 % of 60 %, administrative fine 50 %) and the
  pensioner per-dependant coefficient. The single-claim, input-driven
  computation remains as a fallback.
* Precedence: the register is used only for employees who actually have an
  order on file. Installing ``l10n_cssk_hr_payroll_garnishment_base`` does not
  disable the input-driven path for everyone else, so a site can migrate
  employee by employee. Where an employee has both, the register wins and the
  payslip inputs are ignored.

19.0.1.5.2 (2026-07-08)
=======================

* **Hourly wage support** in the BASIC rule: when the contract ``wage_type`` is
  ``hourly`` (e.g. a DoBPŠ student paid per hour), BASIC = actual worked hours
  (WORK100) × hourly wage, with no day-proration. Monthly contracts are
  unchanged. Lets a student's payslip show the real worked hours (7.5, 13, …)
  instead of a full-time month.

19.0.1.5.1 (2026-07-08)
=======================

* **2025 monthly income-tax band fixed**: the 19%/25% monthly boundary was the
  stale 2024 figure (3961.50); corrected to 4036.79 (= 176.8 × ŽM 273.99 / 12),
  consistent with the annual band.

19.0.1.5.0 (2026-07-08)
=======================

* MRP-validated corrections (reconciled to the cent against filed Data Dance
  payroll, mrpmapd.phc, 2024-2026):

  - **NČZD**: monthly advances now apply the full monthly non-taxable part; the
    §11 ods. 2 high-income taper is annual-only (§35), was wrongly applied monthly.
  - **Per-component floor rounding** of every social and health premium to the
    eurocent (§138 z. 461/2003, §19 z. 580/2004), was half-up.
  - **Dohoda health exemption**: new field ``l10n_sk_health_exempt`` (štátny
    poistenec — student/pensioner) zeroes health insurance on agreement income.
  - **Guarantee exemption**: new field ``l10n_sk_guarantee_exempt`` (≥50%
    statutory owner, §102) zeroes the employer guarantee premium.
  - **2024 statutory constants** backfilled (employer health 11 %, ZŤP 5.5 %,
    NČZD 470.54, tax bands, max base 9128, subsistence minimum, social rates).

19.0.1.4.3 (2026-07-07)
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

19.0.1.4.2 (2026-07-07)
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
  (``action_with_unused_accruals='lost'``, ``can_be_carryover=False``) and are
  deliberately left unchanged. New multi-year forfeiture test in
  ``tests/test_sk_dovolenka_accrual.py``.

19.0.1.4.1 (2026-07-07)
=======================

* Made the leave accrual-plan names translatable. Core ships
  ``hr.leave.accrual.plan.name`` as a plain, non-translatable ``Char``; a small
  model override (``models/hr_leave_accrual_plan.py``) redefines it as
  ``translate=True`` (same low-risk core-field override already used for
  ``hr.leave.type.country_id``). The shipped statutory dovolenka / OČR /
  work-obstacle plan names now carry a clean English source plus a Slovak
  (``sk``) translation in ``i18n/sk.po``; regenerated ``i18n/<module>.pot``.

19.0.1.4.0 (2026-07-07)
=======================

* Country-scoped the payroll and time-off configuration, like the accounting
  localization: ``hr.payroll.structure`` gains a ``country_id`` (and its
  ``company_id`` is relaxed to optional so a structure can be country-global);
  the shipped salary structure is set to country SK with no company, and every
  SK leave type carries country SK (company left empty). Global record rules
  now filter the salary-structure list, the time-off configuration and the
  ``struct_id`` selection to the country of the user's active company, so an SK
  company only sees SK (and country-global) config. Accrual plans have no
  ``country_id`` in core and are scoped indirectly through their
  (country-scoped) leave type.

19.0.1.3.1 (2026-07-06)
=======================

* i18n pass: normalized all user-facing source strings to clean English (field labels, help tooltips, selection options, salary-rule / leave-type / accrual-plan / rule-parameter data names, view group labels), removing mixed-language parentheticals while keeping genuine token abbreviations (NČZD, ZŤP, DoVP, DoPČ, OOP, DVZ, PN, OČR, DDS). Added ``i18n/<module>.pot`` and a complete Slovak ``i18n/sk.po``.

19.0.1.3.0 (2026-07-06)
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

19.0.1.2.0 (2026-07-06)
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
  ``maximum_leave_yearly`` caps each year at the statutory figure, ``can_be_carryover``
  lets unused days carry over (§113). Proration assumption documented in the data
  file. The §105 "dovolenka za odpracované dni" (1/12 per 21 worked days when
  <60 days worked) and the 33+/child eligibility (§103 ods. 2) are NOT derivable
  from payroll data — assign the plan per employee manually. New demo: a start-of-
  year 20-day allocation on the demo holiday type.

19.0.1.1.0 (2026-07-05)
=======================

* Annual tax reconciliation (ročné zúčtovanie preddavkov na daň, §38 zákona
  č. 595/2003 Z. z.): new ``l10n.sk.tax.reconciliation`` model per (employee,
  year) that gathers the year's Σ tax base / Σ advances / Σ child bonus from the
  monthly payslips, recomputes the annual tax with the annual NČZD (taper),
  annual bands, NČZD na manželku, DDS (III. pilier, capped 180 €) and the annual
  child-bonus entitlement, and yields a preplatok/nedoplatok. The result is
  posted onto the reconciliation-month payslip via the input-driven
  ``ANNUAL_TAX_SETTLEMENT`` rule; standard monthly payslips are unchanged. New
  dated parameters ``l10n_sk_nczd_annual``, ``l10n_sk_income_tax_bands_annual``,
  ``l10n_sk_dds_annual_cap`` (2025 & 2026). The annual health-insurance
  reconciliation stays out of scope (insurer-side, §19 zák. 580/2004).

19.0.1.0.0 (2026-07-05)
=======================

* Port to Odoo 19.0. A contract is now an ``hr.version`` record: the Slovak
  payroll fields move from ``hr.contract`` to ``hr.version`` and are whitelisted
  for copy-from-template; the employee mirrors become delegated (``inherited``)
  related fields via ``version_id``; the form view retargets to the contract
  template (``hr.version``) form. The salary rules, dated ``hr.rule.parameter``
  mechanism and absence/leave integration are unchanged (OCA ``payroll`` 19.0
  does not ship ``hr.rule.parameter``, so the module keeps its own).

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

19.0.1.7.0 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* **The social-insurance fund set now follows the INCOME REGULARITY,
  not the kind of agreement.** Sickness, unemployment and the
  short-time contribution were skipped for every DoVP and charged on
  every DoPČ, on the assumption that DoVP means irregular income and
  DoPČ regular. Neither holds: both agreements can lawfully be agreed
  either way, and it is the regularity of the remuneration that
  decides the fund set. A DoVP paid monthly is a zamestnanec s
  pravidelným príjmom and was being under-charged; a DoPČ paid once on
  completion was being over-charged.
* New ``l10n_sk_income_regular`` on the contract carries it. A stored
  editable compute rather than a plain default, so a record created
  programmatically gets the usual treatment for its agreement kind
  instead of silently inheriting a default that is wrong for it.
* ``DoBPŠ`` (dohoda o brigádnickej práci študentov) added as a third
  agreement type.
* ``l10n_sk_agreement_hours_warning`` flags a contracted working time
  above the statutory ceiling: 350 h/year for DoVP, 10 h/week for
  DoPČ, 20 h/week for DoBPŠ (§§ 226, 228a, 227 Zákonníka práce).

19.0.1.8.0 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* Salary rules now ask the applicability table in
  ``l10n_sk_hr_payroll_base`` which contributions and entitlements
  apply to this employment form, instead of each re-deriving it from
  the agreement type. The rule states the question
  (``l10n_sk_applies('SICKNESS_INSURANCE')``) and the answer lives in
  one readable table.

19.0.1.9.0 (2026-08-04)
~~~~~~~~~~~~~~~~~~~~~~~

* The Slovak employment form is now ONE choice: picking the structure sets
  the contract's agreement type, and a constraint rejects a contract
  that disagrees with it. Four forms ship — pracovný pomer, DoVP,
  DoPČ, DoBPŠ.
* Driven by a stored compute rather than an onchange: an onchange
  never runs on create, so an imported or programmatically created
  contract would sit on the DoPČ structure still calling itself
  employment and be rejected at the point of creation.

[19.0.1.18.2] — 2026-09-13
--------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak screen. The template and the catalogues now carry them,
  and the Slovak is written.

[19.0.1.18.3] — 2026-09-13
--------------------------

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

