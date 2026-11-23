=========
Changelog
=========

Unreleased
----------

* **19.0.1.7.0 (2026-11-21):** several employee records of one person taxed
  together (§ 35 ods. 1 zákona 595/2003 Z. z.), for both engines.
  ``hr.employee`` gains ``l10n_sk_tax_principal_id`` (*Taxed Together With*:
  same company, no chains, the same birth number where both have one) and
  ``l10n_sk_tax_linked_ids``. ``l10n.sk.payslip.joint.tax.mixin`` holds
  what a payslip needs: ``_l10n_sk_monthly_tax_base`` (the base of the
  month's advance and of the child bonus), the informative lines
  ``TAXBASE_MOVED`` and ``TAXBASE_TAKEN``, and the checks before computing,
  confirming, cancelling, refunding and deleting; an engine says which
  payslips are confirmed and which are refunds.
  ``l10n_sk_garnishment_net_wage`` refuses a payslip that is taxed together.

* **19.0.1.7.0 (2026-11-21):** ``hr.version`` holds the rule that one
  person has the taxpayer's declaration signed on one employee record of a
  company at a time (§ 36 ods. 6 zákona 595/2003 Z. z.), for the box each
  engine defines: ``_l10n_sk_check_single_tax_declaration`` for the engines'
  constraint, ``_l10n_sk_tax_declaration_conflicts`` and
  ``_l10n_sk_tax_declaration_offenders`` to list what breaks it, and
  ``birth_number_key``, the digits of a birth number, as the key of a
  person.

* **19.0.1.6.4 (2026-11-21):** ``worked_days`` gives the salary rules of
  both engines the worked-day lines of one payroll code as one:
  ``WorkedDayTotal`` holds the days and hours of all the lines (and their
  amount, on the Enterprise engine, whose lines carry one) and reads anything
  else from the first; ``worked_day_totals(lines)`` returns one for each
  code with several lines, so a code with one line stays that line. Moved
  from ``l10n_sk_hr_payroll_oca`` unchanged in behaviour.

* **19.0.1.6.4 (2026-11-21):** ``meal_days.shift_earns_meal`` and
  ``count_meal_days`` take ``any_work``: for an employer who provides the
  meal on a shorter shift too (§ 152 ods. 9 Zákonníka práce, the engines'
  contract field ``l10n_sk_meal_short_shift``) the hours to exceed are none,
  so a day earns the meal when any work was done on it and a day without
  work earns none. The same tolerance applies: a ten-billionth of an hour is
  not work.

* **19.0.1.6.4 (2026-11-21):** the guide's section on the insurance bases
  kept with payroll says that both engines keep and read them
  (``l10n_sk_hr_payroll_ee`` 19.0.1.28.4), what each of the four insurance
  statements takes from them and what it does for a period with a payslip
  that has none. Text only.

* **19.0.1.6.3 (2026-11-21):** ``meal_days`` holds the decision of § 152
  ods. 2 Zákonníka práce for both engines: ``shift_earns_meal(hours,
  min_hours)`` is true for more than ``min_hours`` worked on a day, exactly
  that many earn none, and lengths closer than a millionth of an hour
  (``HOURS_TOLERANCE``) are the same length, so 3.9999999999 and
  4.0000000001 are four hours; ``count_meal_days`` decides each day alone;
  ``whole_days`` is for worked-day lines typed by hand, which hold a total
  and no days. The number of hours is the engines' dated parameter
  ``l10n_sk_meal_min_hours``.

* **19.0.1.6.3 (2026-11-21):** the net wage of a garnishment
  (``garnishment.NET_WAGE_CATEGORIES``) also holds the category ``SICKCOMP``,
  the employer's sick pay: § 89 ods. 1 Exekučného poriadku applies the
  deductions from wages to income that replaces the remuneration for work
  and names the náhrada príjmu pri dočasnej pracovnej neschopnosti. The
  salary rule that asks for the net wage has to run after the sick pay rule.

* **19.0.1.6.3 (2026-11-21):** ``garnishment.garnishment_net_wage`` and the
  rule helper ``payslip.l10n_sk_garnishment_net_wage(categories)`` are the one
  definition of the net wage a garnishment is computed from, for both payroll
  engines and for the payslip input and the order register alike: the lines
  of the categories ``GROSS``, ``SOCIALEMPLOYEE`` and ``INCOMETAX``, that is
  the wage less the employee's premiums (the health minimum top-up among
  them) and the tax advance (§ 69 ods. 1 Exekučného poriadku). The child tax
  bonus is no term: it is not wage (§ 118 ods. 2 Zákonníka práce), so the
  advance deducted is the one before the bonus. The guide says so.

* **19.0.1.6.2 (2026-11-21):** ``l10n_sk_pn_determined_daily_base`` covers a
  new employee (§ 8 ods. 4 and 6 zákona 462/2003 Z. z.): under 90 days the
  period to the day before the incapacity, with the part of that month taken
  from its own payslip where the incapacity lasts to the month's end, and
  ``sick_pay.probable_daily_base`` for an incapacity on the first day or a
  period without a base. ``False`` still means that the *PN_DVZ* input is
  required; ``_l10n_sk_pn_missing_base_message`` words that for the payroll
  officer and each engine shows it. The engines supply the GROSS of the
  computation in progress and the wage a contract would pay for a month. The
  bases of the period are summed as decimals.

* **19.0.1.6.2 (2026-11-21):** ``public_holiday.ABSENCES_OVER_A_PUBLIC_HOLIDAY``
  and ``absence_keeps_public_holiday(code)`` name the absences that keep a
  public holiday falling inside them (sickness, nursing, maternity,
  paternity, parental and unpaid leave); in paid leave the holiday is not a
  day of leave (§ 112 ods. 3 Zákonníka práce). The guide describes public
  holidays in payroll.

* **19.0.1.6.1 (2026-11-21):** ``wage_rounding.round_wage_component(amount)``
  and the rule helper ``payslip.l10n_sk_round_wage_component(amount)`` round
  a wage component up to the cent (owner's decision of 2026-11-21). § 130
  ods. 1 Zákonníka práce rounds the wage paid out upward and has no rule for
  a single component, so each component is rounded in the direction that
  can never take a fraction of a cent from the employee. It is applied once
  to the exact result for the whole period; a whole-cent amount stays that
  cent, also when binary arithmetic delivers it a hair above.

* **19.0.1.6.1 (2026-11-21):** the guide said the health *odpočítateľná
  položka* is not prorated for a part month; the rules reduce it for the
  calendar days outside the contract (§ 16 ods. 18 zákona 580/2004 Z. z.).
  Text only.

* **19.0.1.6.0 (2026-11-21):** ``sick_pay.decisive_period`` and
  ``daily_assessment_base``, and on the payslip
  ``l10n_sk_pn_determined_daily_base(onset)``: the employer's daily assessment
  base from the confirmed payslips of the decisive period, or ``False``
  whenever they do not cover it completely (a missing, part-month, second or
  refunded payslip, an employment under 90 days ending inside a month, no
  base). Each engine supplies its confirmed states and its leave-code path.

* **19.0.1.5.0 (2026-11-20):** ``hr.version.l10n_sk_agreement_oop_applies(day)``
  dates the agreement OOP by § 227a zákona 461/2003 Z. z. for the salary
  rules of both engines: the notice (ods. 3), the ground of maternity,
  paternity or parental leave from 1 January 2027 on a DoVP or DoPČ, and the
  end of that leave (ods. 4). The recorded fund profile stores whether the
  OOP applied in the payslip's month rather than whether the box was ticked.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

* **19.0.1.7.0 (2026-11-21), not yet on 18.0:** the single declaration of
  one person at one employer, with the engines' constraint.

* **19.0.1.6.4 (2026-11-21), not yet on 18.0:** ``any_work`` of
  ``meal_days``, with ``meal_days`` itself.

* **19.0.1.6.4 (2026-11-21), not yet on 18.0:** ``worked_days``, with the
  engine code that reads it.

* **19.0.1.6.3 (2026-11-21), not yet on 18.0:** ``meal_days``, with the
  engine code that reads it.

* **19.0.1.6.2 (2026-11-21), not yet on 18.0:** the daily base of sick pay
  for a new employee and the missing-base message; they extend the
  determined base of 19.0.1.6.0, which is not on 18.0 either.

* **19.0.1.6.2 (2026-11-21), not yet on 18.0:** ``public_holiday``, with
  the engine code that reads it.

* **19.0.1.6.1 (2026-11-21), not yet on 18.0:** ``wage_rounding`` and the
  payslip rule helper, together with the engine rules that call them.

* **19.0.1.6.0 (2026-11-21), not yet on 18.0:** the determined daily
  assessment base of sick pay.

* **19.0.1.5.0 (2026-11-20), not yet on 18.0:** the
  ``l10n_sk_agreement_oop_applies`` helper, on the 18.0 contract model.

* Not yet ported: recorded fund evidence, engine-neutral missing-reader policy
  and explicitly reviewed legacy corrections. Adapt contract/engine adapters
  and rerun signed, optional-module, refund and legacy-review scenarios.

[19.0.1.4.1] — 2026-11-16
-------------------------

Fixed
~~~~~

* **A health minimum top-up without an employee health row was dropped.**
  Finalisation added a computed top-up (OCA ``HEALTHDOPLATOK``, Enterprise
  ``HEALTH_DOPLATOK``) only when an employee health row existed, and otherwise
  stored the other rows without that charge. The payslip is now unrecorded,
  on both engines, so declarations name it. Stored evidence of payslips that
  had the row is unchanged.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

* Not yet on 18.0 (the recorded fund evidence itself is not ported there).

[19.0.1.4.0] — 2026-11-16
-------------------------

Changed
~~~~~~~

* The engine-free half of recording fund bases moved here from the OCA
  bridge, so the Enterprise bridge can share it instead of copying it: the
  in-process capability, the row finalisation (native charge comparison,
  sign by side, duplicates, missing records, the health minimum top-up
  with the engine's own rule code), the evidence assembly and its private
  store, the create/write guard, salary facts, the statutory profile and a
  reader skeleton. Nothing user-visible changes: the stored evidence is
  byte-identical and no engine gains a reader it did not have.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

* Not yet on 18.0 (the recorded fund evidence itself is not ported there).

[19.0.1.3.0] — 2026-11-11
-------------------------

Added
~~~~~

* Engine-neutral signed fund-record shape and abstract identity/salary checks.
  Optional invalid evidence remains missing; the payroll engine owns storage.
  Record strings preserve the actual rule precision for consumer rounding.

[19.0.1.2.2] — 2026-11-10
-------------------------

Fixed
~~~~~

- Floor the employee's daily social-insurance maximum before multiplying
  insured calendar days in a partial month (§ 138(13)). Preserve the whole
  monthly maximum for a full month and leave employer limits unchanged.
- Tests: the Enterprise engine has the same payslip test as the OCA engine
  (16 days of January 2026, employee disability premium 259.56).

[19.0.1.2.1] — 2026-11-10
-------------------------

Fixed
~~~~~

- Shared decimal sick-pay arithmetic: four-place downward daily-base rounding
  and upward eurocent compensation rounding, without binary-float artefacts.

[19.0.1.2.0] — 2026-11-09
-------------------------

Added
~~~~~

- ``l10n_sk_employee_social_cap`` and ``l10n_sk_month_employed_ratio``: the
  employee's maximum assessment base for a part-month employment
  (§ 138 ods. 13 zákona 461/2003), shared by both engines.
- The calendar-day sick-pay split in ``sick_pay.py``.

[19.0.1.1.2] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.1.1] — 2026-10-27
-------------------------

**Changed**

- **Slovak translation.** A Slovak catalogue is added for its few labels.

[19.0.1.1.0] — 2026-10-27
-------------------------

**Fixed**

- The applicability table knows the worker's pension: § 4 ods. 1 písm. b) (no sickness or unemployment insurance on a DoVP/DoPČ with a dôchodok), § 19 ods. 3 písm. b) (no unemployment insurance after a starobný, predčasný starobný or over-70 % invalidný dôchodok) and § 128 ods. 3 (no disability premium after a starobný or predčasný starobný dôchodok, or a výsluhový one at pension age). The workaround of unticking *Regular monthly income* for a pensioner is no longer needed.
- The short-time work contribution applies to a pracovný pomer only (§ 128 ods. 1 písm. g) zákona 461/2003), not to a dohoda with a regular income.

[19.0.1.0.1] — 2026-10-27
-------------------------

**Fixed**

- A student on a **DoBPŠ** is no longer charged sickness or unemployment insurance (nor the short-time work contribution), even with a regular monthly income: § 4 ods. 1 písm. a) zákona 461/2003 takes the DoBPŠ out of the definition of a zamestnanec for those funds, and with a regular income the student is pension-insured only (§ 4 ods. 2 písm. b) bod 1). Applies to both payroll engines.
- Pensioners on a DoVP/DoPČ (§ 4 ods. 1 písm. b)) are still charged, because the contract records no pension status; untick *Regular monthly income* for them.
- The note on wage surcharges cites the paragraphs § 223 ods. 2 ZP actually extends to dohody (§§ 122a, 122b, 123; there is no § 122c).

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
