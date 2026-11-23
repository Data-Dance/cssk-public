=========
Changelog
=========

Unreleased
==========

- **19.0.1.29.1 (2026-11-22):** the employee form offers the salary structures shipped here. OCA
  payroll limits the *Salary Structure* field to the structures of the
  employee's own company, and the shipped ones belong to no company, so
  none could be picked and typing a name created an empty structure.
  Found by opening the form in a browser.
  The warning about an agreement's working time no longer mixes English
  (*per year*, *per week*) into the Slovak or Czech sentence.

- **19.0.1.29.0 (2026-11-21):** the annual tax reconciliation is the
  taxpayer's, not the employee record's.

  * A reconciliation made for a record that taxes the month for others
    gathers the year's payslips of all those records: two months of the
    example give bases of 2 × (342.40 + 256.80) = 1 198.40 and
    advances of 2 × 19.37 = 38.74. The children are still read from
    that record itself.
  * For a linked record alone it is refused, with the record to make it
    for. Two records with the same birth number cannot each have one for
    the same year (§ 38 zákona 595/2003 Z. z.): the second is refused, and
    the message says to link the records so that one gathers both. Checked
    when a reconciliation is saved; existing ones are not touched.
  * The annual report and the certificate of income still give each
    employee record a column of its own.

- **19.0.1.29.0 (2026-11-21):** several employee records of one person are
  taxed together, where the payroll officer says so.

  * § 35 ods. 1 zákona 595/2003 Z. z.: „Zdaniteľnou mzdou je úhrn
    zdaniteľných príjmov zo závislej činnosti zúčtovaných a vyplatených
    zamestnancovi za kalendárny mesiac ..., znížený o a) sumy zrazené na
    poistné a príspevky, ktoré je povinný platiť zamestnanec, b) nezdaniteľnú
    časť základu dane na daňovníka“. Each payslip was taxed alone: an
    employment of 400 with the declaration and a DoPČ of 300 beside it paid
    0.00 and 48.79, where the tax of the month's total is (342.40 +
    256.80 − 497.23) × 19 % = 19.37. No authority says in so many
    words how two relationships at one employer are taxed, so nothing is
    inferred: the employee record gains *Taxed Together With*.
  * The payslip of a record linked this way computes its pay, premiums
    and tax base as before and no non-taxable amount, tax or child bonus;
    the line *Tax Base Taxed on the Other Record's Payslip*
    (``TAXBASE_MOVED``) shows the base. The payslip of the record named adds
    those bases of the same month (line ``TAXBASE_TAKEN``), floors the total
    at zero once and computes on it the one non-taxable amount, the bands and
    the child bonus with its limit: 19.37 in the example; one child under
    15 keeps the whole 100.00 (29 % of 342.40 alone gave 99.30); 3 000
    and 2 500 are taxed 832.78 with the excess over 3 665.28 at 25 %
    (alone 393.45 and 406.60).
  * Order: the linked payslips are computed first, in one batch by
    themselves. The payslip that taxes the month refuses to be computed
    while a linked payslip of the month is not, and to be confirmed when
    the linked payslips no longer hold what it took over. Once it is
    confirmed, a linked payslip of the month cannot be changed, cancelled,
    refunded or deleted, and no new one computed; refund the confirmed
    payslip first. A confirmed payslip is never changed.
  * A refund and the payslip it refunds are both left out of the sums.
    The link cannot be changed between the two confirmations of a month. A
    linked record is taxed on its own in a month in which no contract of
    the other record runs. Where the record that taxes the month has two
    payslips in it, the first computed takes the bases over.
  * A wage garnishment is refused on payslips taxed together: it is
    deducted from the person's whole net wage from the employer (§ 69
    Exekučného poriadku), which one payslip does not hold.
  * Nothing changes until a link is set.

- **19.0.1.29.0 (2026-11-21):** one declaration of the taxpayer for one
  employer.

  * § 36 ods. 6 zákona 595/2003 Z. z. has the employee give the
    declaration to an employer, and § 35 ods. 1 písm. b) takes the
    non-taxable amount once off what the employer pays in the month. An
    employment and an agreement of one person are two employee records
    here, and *Tax Declaration Signed* could be ticked on both: each payslip
    then took the whole non-taxable amount. 400 in an employment and 300 in a
    DoPČ, both ticked, were taxed 0.00 where the month's tax is 19.37.
  * Among the employee records of one company with the same birth number
    the box can now be ticked on one contract version valid on a given day.
    Records without a birth number, records of different companies and
    contracts that do not share a day are not matched; the slash of a birth
    number does not matter.
  * The rule is checked when a record is saved. An update does not check
    it and cannot fail on it: it lists every pair that breaks the rule
    already in the server log (*the taxpayer's declaration is signed twice
    for one birth number*), with both employees and the dates of the
    versions. Such a pair is refused the next time one of its versions is
    saved, with a message naming the other record.
  * No payslip changes.

- **19.0.1.28.4 (2026-11-21):** an option for an employer who provides the
  meal on a shorter shift.

  * § 152 ods. 9 Zákonníka práce: „Zamestnávateľ môže po prerokovaní so
    zástupcami zamestnancov ... c) rozšíriť okruh fyzických osôb, ktorým
    zabezpečí stravovanie, a ktorým bude prispievať na stravovanie podľa
    odseku 3.“ An employer who does so had only *Meal Days / Month* to say
    it with, a fixed number that does not follow the absences.
  * New on the contract, off by default: *Meal also for a Shift of Four
    Hours or Less* (``l10n_sk_meal_short_shift``). With it a day earns the
    meal when any work was done on it; a day without work, on leave or on a
    public holiday, still earns none, and there is one meal a day. The rest
    of the count is as it was, the whole days of worked-day lines typed by
    hand included, and a number in *Meal Days / Month* is still taken as it
    is.
  * June 2026, 22 days, 5.12 a day: a schedule of four hours a day earns
    22 meals and 112.64 with the option (none without); half a day of leave
    on an eight-hour day leaves 22 (21 without); a whole day of leave leaves
    21 and 107.52 either way.
  * The decision is the ``any_work`` argument of ``meal_days`` in
    ``l10n_sk_hr_payroll_base``, the same for both engines.

- **19.0.1.28.4 (2026-11-21):** the object that gives the rules all the
  worked-day lines of a code now lives in ``l10n_sk_hr_payroll_base``
  (``worked_days.WorkedDayTotal``, ``worked_day_totals``), where the
  Enterprise overlay reads it too. Nothing changes on this engine.

- **19.0.1.28.3 (2026-11-21):** leave types that share a Slovak payroll
  code are paid together.

  * Each leave type has a worked-day line of its own on the payslip, and
    several starter types share a code: unpaid leave and unpaid leave for
    education are NEPLATENE, sickness and quarantine are PN, and the paid
    obstacles are OBSTACLE. The rules were handed one line per code, so
    with two types of a code in one payslip only one of them counted.
  * The rules now read the days and hours of all the lines of a code,
    whatever built the lines: the calendar, an earlier version of the
    module, or a hand. The lines themselves stay as they are, one per leave
    type.
  * June 2026, 22 days of eight hours on 2 000: a day of unpaid leave and a
    day of unpaid leave for education give a salary of 2 000 x 160 / 176 =
    1 818.19 (was 1 909.10, one of the two days paid). Sick for two
    scheduled days and in quarantine for three: 2 000 x 136 / 176 =
    1 545.46 (was 1 727.28). A paid obstacle, a blood donation and paid
    leave for education, a day each: salary 1 727.28 and 24 hours of
    compensation, 272.73 (was 1 909.10 and 8 hours, 90.91).
  * The sick pay, the meal days and the worked time of the average earnings
    were right before: they do not read the lines by code.
  * The update recomputes nothing. A draft payslip with such absences takes
    the right amounts when it is computed again, without its worked days
    being rebuilt; a confirmed payslip stays as it is.

- **19.0.1.28.3 (2026-11-21):** a meal day is a day with more than four
  hours worked.

  * § 152 ods. 2 Zákonníka práce gives the meal, or the financial
    contribution, to an employee „ktorý v rámci pracovnej zmeny vykonáva
    prácu viac ako štyri hodiny“. The meal days of a payslip were the days
    worked added up, parts of days included: an afternoon closed in the
    calendar gave 21.5 meal days in a month of 22, and half a day of leave
    on two days took one meal day where two shifts fell to four hours.
  * Each scheduled day of the period is now decided alone. Its scheduled
    hours, less the hours of absence and of a public holiday on that day,
    must exceed the new dated parameter ``l10n_sk_meal_min_hours`` (4).
    June 2026, 22 days of eight hours at 5.12 a day: an afternoon closed in
    the calendar, or half a day of leave, gives 21 days and 107.52 (was 21.5
    and 110.08); half a day of leave on two days gives 20 and 102.40 (was 21
    and 107.52); two hours at the doctor's leave six hours worked, 22 days
    and 112.64 (was 21.75 and 111.36). A whole month is 22 days as before.
  * A schedule of four hours a day earns no meal (it earned one every day):
    no shift has more than four hours of work. Where the employer provides
    one all the same (§ 152 ods. 9), set *Meal Days / Month* on the
    contract; that number is taken as it is, as before.
  * The second meal for a shift of more than 11 hours is the employer's
    option (§ 152 ods. 2) and is not counted.
  * Overtime and work on a public holiday are inputs with hours and no day,
    so they are not in the hours of a day; a public holiday is a day without
    work.
  * A day is the calendar day of the schedule, so a night shift scheduled
    over two days is counted as two days.
  * Worked-day lines that do not hold the hours the calendar and the
    absences give were typed by hand, or are older than an absence. They do
    not say which days were worked: their whole days count (19.5 days are
    19).
  * The update recomputes nothing. A draft payslip takes the new count when
    it is computed again; a confirmed payslip stays as it is.

- **19.0.1.28.3 (2026-11-21):** the employer's sick pay is part of the net
  wage a garnishment is computed from. § 89 ods. 1 Exekučného poriadku
  applies the deductions from wages to income that replaces the remuneration
  for work and names the náhrada príjmu pri dočasnej pracovnej neschopnosti;
  the rule left it out, so in a month with sick pay less was deducted than
  the claim could reach. Sick pay of 74.00 next to a net wage of 1 134.51
  gives 1 208.51 to compute the deduction from. The rule ``GARNISHMENT`` moves
  from sequence 176 to 179, after ``SICK_COMP``, on the payslip input and
  with an order in the register alike.

- **19.0.1.28.3 (2026-11-21):** the net wage a garnishment is computed from
  no longer contains the child tax bonus. § 69 ods. 1 Exekučného poriadku
  takes the wage less the tax advance and the premiums, and the daňový bonus
  is not wage (§ 118 ods. 2 Zákonníka práce); the Ministry of Justice says
  the same in its opinion on deductions from income that does not replace the
  remuneration for work. The rule added the whole bonus. July 2026, wage
  1 500.00, two children, two dependants: premiums 216.00, advance before
  the bonus 149.49, net wage 1 134.51 and a deduction of 171.52 for an
  ordinary claim, where it was 1 334.51 and 238.19; the bonus of 200.00 is
  paid on top in full, NET 1 162.99. The same on the payslip input and with
  an order in the register. The rule now reads the net wage from
  ``payslip.l10n_sk_garnishment_net_wage(categories)`` of
  ``l10n_sk_hr_payroll_base`` 19.0.1.6.3, one definition for both engines.
  An upgrade changes draft payslips when they are recomputed; confirmed ones
  stay.

- **19.0.1.28.2 (2026-11-21):** the daily base of the employer's sick pay
  for a new employee (§ 8 ods. 4 and 6 zákona 462/2003 Z. z.), determined in
  ``l10n_sk_hr_payroll_base``.

  * Under 90 days of employment the decisive period runs from its start to
    the day before the incapacity (§ 8 ods. 4). The part of the month of the
    incapacity is that month's own sickness base, where the incapacity lasts
    to the end of the month or of the employment, so that all of it was
    reached before the incapacity. Hired 1 March 2026 on 2 000, sick 20 to
    30 April: (2 000.00 + 1 181.82) / 50 days = 63.6364 and 327.73 of sick
    pay; hired 10 March, sick 25 to 31 March: 1 000.00 / 15 = 66.6666 and
    196.67.
  * Sick on the first day, or with no base in the period: the base premium
    would be paid on in the month the incapacity began (§ 8 ods. 6), the
    monthly wage (an hourly rate over the month's scheduled hours) under the
    monthly maximum, over the days of that month. Hired 1 June 2026 and sick
    that day: 2 000 / 30 = 66.6666.
  * Still to be typed in as *PN_DVZ*: an employee of under 90 days who was
    back at work in the month of the incapacity (the wage of that month
    would have to be split by day), and a first-day incapacity in an
    employment that began inside a month (the Act names no divisor).
  * A payslip that owes sick pay it could not compute says so and cannot be
    confirmed: a warning on the payslip form, and an error on confirmation. It names the employee, the incapacity and the
    *PN_DVZ* input. It used to show no sick-pay line and nothing else.
  * The bases of the decisive period are summed as decimals: 2 000.00 +
    1 181.82 as floats is 3 181.8199999…, which cut the fourth place of the
    daily base to 63.6363.

- **19.0.1.28.2 (2026-11-21):** a public holiday inside an absence, confirmed
  payslips, the annual tax settlement, the garnishment inputs, the child of
  18 or over and the hourly rate.

  * An absence that begins on a public holiday of the working calendar is
    that absence. The whole of it used to be filed as the holiday and paid as
    worked: 2 000 with sickness from 1 to 15 May 2026 paid 2 000.00 and no
    sick pay; it pays 952.39 (2 000 × 80 / 168) and 272.00 of sick pay on a
    daily base of 40. Maternity, paternity, parental, nursing and unpaid
    leave from 1 May paid the full salary and now pay nothing.
  * A public holiday inside paid leave is not a day of leave (§ 112 ods. 3
    Zákonníka práce) and stays inside the monthly wage (§ 122 ods. 3). Leave
    from 27 April to 5 May 2026 paid three days of leave in May; it pays two,
    1 809.53 + 190.48. Leave booked from Good Friday 3 April to 10 April 2026
    is four days of leave, 1 636.37 + 363.64, where the payslip showed no
    leave at all.
  * Which of the two a day is: sickness, nursing, maternity, paternity,
    parental and unpaid leave keep a holiday that falls inside them, and no
    wage is due for it (the employer's sick pay runs by calendar day, § 7
    ods. 2 zákona 462/2003 Z. z.); in paid leave and in an obstacle in work
    the day is the holiday. The list is
    ``ABSENCES_OVER_A_PUBLIC_HOLIDAY`` of ``l10n_sk_hr_payroll_base``.
  * With the OCA module ``hr_holidays_public`` installed, the engine left the
    holidays of the OCA holiday calendar out of the worked days while the
    month's hours kept them, so a whole month worked with one holiday paid
    2 000 × 168 / 176 = 1 909.10 of a salary of 2 000. The worked days of a
    Slovak contract are the whole schedule again; the holiday is inside the
    monthly wage (§ 122 ods. 3).
  * ``compute_sheet`` computes a Slovak payslip only while it is a draft or
    waiting. The engine computes whatever it is given and sets it to waiting,
    so a confirmed payslip called through the API or a batch was recomputed
    on today's contract and left the confirmed state. A confirmed or
    cancelled payslip now stays as it is, with its recorded fund bases.
  * The annual tax settlement keeps a child tax bonus that the employer
    granted during the tax years 2023 and 2024 when the recomputation gives
    less (§ 33 ods. 11 zákona 595/2003 Z. z. as in force to 31. 12. 2024:
    the taxpayer "nestráca nárok na už priznaný daňový bonus"). Zákon
    278/2024 Z. z. replaced the paragraph and its § 52zzzb ods. 6 applies
    the new wording first for January 2025, so from the tax year 2025 the
    difference is still taken back. Tax year 2024, 1 820 granted and 1 680
    recomputed: 0,00, not −140,00. The switch is the dated parameter
    ``l10n_sk_child_bonus_keep_granted``.
  * An underpayment of tax of 5 € or less from the annual settlement is not
    withheld (§ 38 ods. 7 zákona 595/2003): 3,50 used to be withheld. It is
    set off against child bonus still to be paid in the settlement; what the
    bonus does not cover is withheld only when the new box *Assigns a Share
    of Tax (§ 50, § 50aa)* is ticked. A bonus taken back is not such an
    underpayment. The new field *Tax Underpayment Not Withheld* shows the
    amount left unpaid, and the limit is the dated parameter
    ``l10n_sk_tax_underpayment_not_withheld``.
  * The update recomputes the settlements that are not posted yet under
    both rules and leaves a posted settlement as it was posted.
  * The *GARNISHMENT* and *GARNISHMENT_PRIORITY* inputs round the protected
    sums down to the cent, as § 4 nariadenia vlády č. 268/2006 Z. z. says and
    as the garnishment register does: the sum for the debtor, the sum per
    dependant and the limit of § 3 ods. 1. They were rounded to the nearest
    cent, so one claim gave two deductions depending on where it was entered.
    July 2026, living minimum 295.22, two dependants, net wage 1 134.51:
    413.30 + 2 × 103.32 = 619.94 is protected and one third of the rest is
    171.52, not 171.51; in August 2024 (273.99) a wage above the limit was
    deducted 3 cents short. A test compares the input with the register for
    five months, four wages and up to three dependants, and another the living
    minimum and the coefficients of the rule parameters with the register's
    rate records.
  * For January 2023 to December 2024 a dependent child of 18 or over has a
    child tax bonus of 50 € a month (§ 52zzp ods. 4 and 5 zákona 595/2003 Z.
    z.) and counts for the percentage limit of § 33 ods. 6 like every
    dependent child. The contract gains *Children 18y+ (tax bonus to 2024)*
    and the dated parameter ``l10n_sk_child_bonus_over_18`` (50 from 1
    January 2023, 0 from 1 January 2025); the monthly rule and the annual
    settlement read both. 1 000 € in December 2024 with two children under
    18 and one over: 330 limited to 34 % of 866,00 = 294,44. From January
    2025 a number left there gives nothing and does not raise the limit.
  * An hourly wage keeps four decimals. The minimum hourly wage and its
    degree claims have three (§ 2 ods. 2 zákona 663/2007 Z. z., § 120 ods. 7
    Zákonníka práce), and *Hourly Wage (SK)* was an amount in whole cents:
    5,259 was stored as 5,26 and 176 hours paid 925,76 where 925,59 is due
    (925,584 rounded up). The field is now a number with four decimals;
    rates already entered stay as they are. The warning on an agreement
    under the minimum hourly wage sees a rate under it by a fraction of a
    cent, and the probable earnings of an hourly wage are the rate itself,
    not the monthly wage over the month's hours.

- **19.0.1.28.1 (2026-11-21):** corrections to the payslip arithmetic.

  * A monthly salary is prorated in the month the contract ends: the
    worked-day lines stop at the contract end, as they start at its start.
    2 000 with a contract ending on 15 June 2026 was paid 2 000.00 and is
    now 1 000.00.
  * The basic wage of a part month is a whole-cent amount before any levy or
    the tax reads it: 1 000 from 10 March 2026 went into the levies and the
    tax as 727.2727.
  * Every wage component is rounded up to the cent (owner's decision of
    2026-11-21): the base pay, monthly and hourly, the leave pay and the two
    obstacle compensations, which were rounded to the nearest cent. § 130
    ods. 1 Zákonníka práce rounds the wage paid out upward and has no rule
    for a single component, so each component is rounded in the direction
    that can never take a fraction of a cent from the employee. The exact
    result of the formula for the whole period is rounded once
    (``round_wage_component`` of ``l10n_sk_hr_payroll_base``), a whole-cent
    result stays as it is, and a full month is exactly the salary. 1 000
    from 10 March 2026 is 727.28 (727.2727), NET 504.28; 2 000 with one day
    of leave in May 2026 is 1 904.77 (1 904.7619) plus 95.24 of leave pay
    (95.2384), GROSS 2 000.01. The premiums, the overtime pay and the
    minimum wage top-up were rounded up already; levies, tax, child bonus,
    sick pay and meal amounts keep their own rounding.
  * The tax advance and the child bonus are rounded to the cent before NET
    reads them (§ 47 zákona 595/2003 Z. z.), so the lines add up to NET:
    1 238 with the declaration in March 2026 is 1 238 − 178.27 − 106.88 =
    952.85, not 952.86. ``_l10n_sk_monthly_income_tax`` still returns the
    advance before rounding.
  * Several payslip inputs of one code are summed by the rules that read an
    amount or a number of days (the deductions, the reimbursement, the
    garnishment debt, *PN_DAYS*, the annual settlement). Two *DEDUCTION*
    inputs of 50 and 30 deducted 30. *PN_DVZ* is a daily base and is not
    summed.
  * With *Meal Days / Month* at 0 the meal rules count the days worked: the
    scheduled days less the days of absence and the public holidays (§ 152
    ods. 2 Zákonníka práce). They counted every scheduled day.
  * The annual tax of the settlement rounds an exact half cent upward (§ 47):
    19 % of 9 999.50 is 1 899.91, not 1 899.90.
  * The living minimum is 273.99 from 1 July 2024. Its record and the one
    for the first half of 2024 (268.88) shared an XML id, so the second
    overwrote the first and 268.88 applied until 30 June 2025. It feeds the
    protected amount of the *GARNISHMENT* input. An upgrade corrects the
    record and adds the missing one; a test refuses an id declared twice in
    a data file.
  * Meal allowance for 5 to 12 hours: 7.80 on 1 January 2024 (opatrenie MPSVR
    SR č. 368/2023 Z. z., from 1 October 2023) and 8.30 from 1 September 2024
    (č. 211/2024 Z. z.). The data had 7.30 until the end of 2024. An upgrade
    corrects both values.
  * Texts: the monthly allowance is applied in full (the taper of § 11 ods. 2
    is annual), and the employer's sick pay is exempt from income tax (§ 5
    ods. 7 písm. f) zákona 595/2003 Z. z.).

- **19.0.1.28.0 (2026-11-21):** the daily assessment base of the employer's sick
  pay is determined from the confirmed payslips when the *PN_DVZ* input is
  absent (§ 8 ods. 4, 5 and 8 zákona 462/2003 Z. z., § 54 zákona 461/2003):
  the decisive period, the sickness bases of its payslips over its days less
  the excluded leave, four places downward. The input still wins, and is
  still required when the payslips do not cover the period completely; the
  rule ``SICK_COMP`` no longer needs it to run. The logic is in
  ``l10n_sk_hr_payroll_base`` 19.0.1.6.0.

- **19.0.1.27.0 (2026-11-20):** the agreement OOP of a person on maternity,
  paternity or parental leave (§ 227a zákona 461/2003 Z. z. from 1 January
  2027). The contract gains *OOP Ground*, *OOP Notice Received* and *Leave
  Ends (OOP)*; on the ground of leave the OOP applies on a DoVP or DoPČ from
  January 2027, from the notice (ods. 3) to the month the leave ends (ods. 4).
  A claim on the other ground with a notice date follows the same start rule;
  without one it is unchanged. *OOP Agreement (student/pensioner)* is now
  *OOP Agreement*. The salary rules ask
  ``l10n_sk_agreement_oop_applies(payslip.date_from)`` of
  ``l10n_sk_hr_payroll_base`` 19.0.1.5.0 instead of reading the box.

- **19.0.1.26.6 (2026-11-19):** share the OCA monthly income-tax calculation
  for explicit monthly bases, with a taxable-wage rounding hook. The default
  preserves the native payslip calculation.

- **19.0.1.22.0 (2026-11-09), DISCHARGED on 18.0 by 997c7bbb:** the employee social insurance cap is prorated for a part-month (§ 138 ods. 13, employer cap untouched); sick pay and the § 16a minimum count calendar days from the start of the incapacity (§ 8 zákona 462/2003); the health allowance is reduced for a part-month (§ 16 ods. 18).

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **19.0.1.29.0 (2026-11-21), not yet on 18.0:** the single declaration of
  one person at one employer; there the box is on ``hr.contract``.

- **19.0.1.28.4 (2026-11-21), not yet on 18.0:** the option of a meal on
  a shorter shift, with the meal days of 19.0.1.28.3.

- **19.0.1.28.3 (2026-11-21), not yet on 18.0:** the meal days counted
  by shift of more than four hours, with ``meal_days`` of the base module.

- **19.0.1.28.3 (2026-11-21), not yet on 18.0:** the garnishment net wage
  without the child tax bonus.

- **19.0.1.28.2 (2026-11-21), not yet on 18.0:** the public holiday inside an
  absence (``_l10n_sk_leave_pieces``) and the guard of ``compute_sheet`` on a
  confirmed payslip. Check both against the 18.0 engine first. The two rules
  of the annual tax settlement (a child bonus granted in 2023 and 2024 is
  kept; an underpayment of 5 € or less is not withheld) are not on 18.0
  either; the reconciliation model is the same there. Also not on 18.0: the
  rounding of the protected sums of the garnishment inputs. Nor are the child
  of 18 or over and the four decimals of the hourly rate; there the fields go
  on ``hr.contract``.

- **19.0.1.28.1 (2026-11-21), not yet on 18.0:** the payslip arithmetic
  corrections (worked days cut at the contract end, wage components rounded
  up to the cent once, rounded tax and child bonus in NET, summed inputs,
  meal days, the half-up annual tax) and the two 2024 meal allowance values. On 18.0 the contract
  is ``hr.contract`` and the monthly tax is computed inline in the rule;
  reproduce each with its test before porting.

- **19.0.1.28.0 (2026-11-21), not yet on 18.0:** the determined daily
  assessment base of sick pay. On 18.0 the confirmed payslip state and the
  contract model differ; the two engine hooks carry both.

- **19.0.1.27.0 (2026-11-20), not yet on 18.0:** the agreement OOP on the
  ground of maternity, paternity or parental leave — the three contract
  fields (on ``hr.contract`` there), the constraint, the rule condition and
  the ``l10n_sk_agreement_oop_applies`` helper of the base module. Needed on
  18.0 before the January 2027 payroll.

- **19.0.1.26.6 (2026-11-19), not yet on 18.0:** the shared monthly
  income-tax calculation and taxable-wage rounding hook. Port after the
  monthly NČZD and January-pension readers, or adapt the 18.0 inline NČZD
  taper to preserve its existing calculation. OCA engine only.

- **19.0.1.26.5 (2026-11-18), not yet on 18.0:** the monthly tax-facts
  reader and its tests, on the 18.0 contract model. OCA engine only.

- **19.0.1.26.4 (2026-11-18), not yet on 18.0:** the employer PN maximum
  DVZ for 2024–2027 and the native/manual cap regressions. OCA parameter
  model only.

- **19.0.1.26.3 (2026-11-18), not yet on 18.0:** the effective-date
  ambiguity check in the OCA rule-parameter reader and
  ``tests/test_rule_parameter_dates.py`` (native-copy regression included).
  OCA engine only.

- **19.0.1.26.2 (2026-11-17), not yet on 18.0:** the annual January tax-fact
  reader and its tests, on the 18.0 contract model. OCA engine only.

- **19.0.1.26.1 (2026-11-17), not yet on 18.0:** the monthly wage hook and
  the probable-earnings fallback together; on 18.0 the contract is
  ``hr.contract``. OCA engine only.

- Not yet ported: mirror the five OOP-before-maximum changes in both engines
  and rerun the year-boundary, unaffected-fund and tax/net-effect checks.

- Not yet ported: recorded fund evidence, engine-neutral missing-reader policy
  and explicitly reviewed legacy corrections. Adapt contract/engine adapters
  and rerun signed, optional-module, refund and legacy-review scenarios.

- **19.0.1.24.6 (2026-11-11), not yet on 18.0:** the 9.80 € stravné from
  1. 12. 2026. Data only; the parameter code is the same on 18.0.
  **DISCHARGED 2026-11-16 — do not port this again**: on 18.0 as
  18.0.2.9.1 (fdf9ffcce).

- **19.0.1.24.4 and 19.0.1.24.5 (2026-11-10), not yet on 18.0:** employer
  sick pay clipped to the employment and on the onset's terms
  (cssk-public#39), and the starter leave types as noupdate data
  (cssk-public#40). On 18.0 the employment dates are on ``hr.contract``.
  **DISCHARGED 2026-11-16 — do not port this again**: sick pay on 18.0 as
  18.0.2.9.3 (f6d4a1b7e, both engines); the OCA starter leave types were
  already noupdate on 18.0 (regression test added there, 3ebf05dbd covers
  Enterprise).

- **19.0.1.24.2 and 19.0.1.24.3 (2026-11-10), not yet on 18.0:** sick pay
  only where the agreement is sickness-insured (cssk-public#31), and the
  average's worked time without absences (cssk-public#32). Check how the
  18.0 engine's worked days carry leave before porting the second.

- **19.0.1.24.1 (2026-11-09), not yet on 18.0:** hourly BASIC removes approved
  absence hours before separate leave compensation is added. Before porting
  to 18.0, review that engine's paid-time source; do not subtract absence
  twice from an already net amount.

- **19.0.1.24.0 (2026-11-09), not yet on 18.0:** the § 134 average
  (21 days or 168 hours, company and employment isolation, credit notes;
  cssk-public#28). On 18.0 the employment key is the contract.

- **19.0.1.23.0 (2026-11-09), not yet on 18.0:** no monthly NČZD for a
  § 11 ods. 6 pensioner on 1 January (cssk-public#24, plus the rehire
  fix). On 18.0 the flag goes on ``hr.contract`` and the January contract
  is the one running on 1 January (for a hire, the first contract of the
  year); the salary rule's localdict key is ``contract``.

- **19.0.1.21.1 (2026-11-08), not yet on 18.0:** the RZD reads only
  confirmed payslips of its own company, keyed by period end
  (cssk-public#20). On 18.0 the confirmed state is ``done`` as well; port
  ``tests/test_rzd_sources.py`` with ``contract_id`` for the version.
- **19.0.1.21.0 (2026-11-08), not yet on 18.0:** the pensioner NČZD in
  the RZD (§ 11 ods. 6). On 18.0 the field goes on ``hr.contract`` and the
  RZD reads the contract running on 1 January.
- **19.0.1.19.4 (2026-11-05), not yet on 18.0:** the EUR 300 agreement OOP
  from 1. 1. 2027 (``rule_parameter_dohoda_oop_2027``). Data only; the 18.0
  rules read the same parameter. **DISCHARGED 2026-11-05 — do not port this
  again**: on 18.0 as 18.0.2.7.1 (merge 3d2a6d07).
- **19.0.1.20.0 (2026-11-06), not yet on 18.0:** the dated 2027 parameter
  values (maximum base, health minimum base, NČZD and its taper, tax bands,
  child-bonus taper, minimum hourly wage, maximum DVZ, seasonal OOP 810) and
  ``tests/test_parameters_2027.py``. Data only; the 18.0 parameters carry the
  same codes, so the records port as they are. Adapt the test to the 18.0
  contract (``contract_id``) and payslip states.
  **DISCHARGED 2026-11-16 — do not port this again**: on 18.0 as
  18.0.2.10.0 (fd65fb927). Two tests stay 19.0-only (annual NČZD taper
  above the threshold, 2027 health minimum top-up): they need 19.0's
  ffd67cd0c, which 18.0 still lacks, so 18.0's taper is wrong for 2026 too.
  **Fully DISCHARGED 2026-11-16**: ffd67cd0c and both tests are on 18.0 as
  18.0.2.10.1 (48c3c03a0); the DoBPŠ part stays 19.0-only on the OCA engine
  (18.0 has no DoBPŠ agreement type).

[19.0.1.26.5] — 2026-11-18
==========================

Added
~~~~~

* ``_l10n_sk_monthly_tax_facts(version, *, include_january=False)``: one
  cooperative reader for the dated facts the monthly NČZD uses (company,
  employee, version, year, cut-off, signed declaration and, on request, the
  January pension facts), returned as a detached dictionary. Evidence readers
  call it instead of duplicating the allowance policy. The monthly NČZD keeps
  its company/employee check, its early exit for an unsigned declaration and
  the January company/pension-consistency checks. OCA engine only.
  Contributed by votrelec (cssk-public#56).

[19.0.1.26.4] — 2026-11-18
==========================

Fixed
~~~~~

* Employer sick-pay maximum DVZ for 2024–2027. Apply the four-place
  downward rounding in 462/2003 section 8(7)-(8), independently from the
  Social Insurance Agency sickness-benefit ceiling. The 2024 value also uses
  the 2022 general assessment base. Recalculation of retained payroll
  remains an explicit correction workflow.
  Contributed by votrelec (cssk-public#55).
* The Enterprise engine carries the same four values from
  ``l10n_sk_hr_payroll_ee`` 19.0.1.26.2.

[19.0.1.26.3] — 2026-11-18
==========================

Fixed
~~~~~

* Conflicting rule-parameter definitions at the same effective date are
  rejected. The reader no longer lets database row order pick one of them:
  matching legacy rows remain readable, conflicting ones raise an error that
  names the parameter and the date, and earlier and later dates are checked
  independently. No definition, payslip or retained evidence is rewritten by
  the reader. OCA parameter model only; Enterprise refuses such a tie at
  entry with a unique key on the parameter and the date.
  Contributed by votrelec (cssk-public#54).
* An integer and a decimal with the same value (``1`` and ``1.0``) on one
  date count as matching; a boolean and a number still conflict.
* The reader finds a tie in its first query (two rows instead of one), so
  a parameter without a tie is still read with one search.

[19.0.1.26.2] — 2026-11-17
==========================

Added
~~~~~

* ``_l10n_sk_annual_january_tax_version()``: one cooperative reader for the
  January tax fact of the annual reconciliation, used by both the pension
  default and the annual computation. The default delegates to the dated
  employee reader and keeps the draft fallback; an extension can supply a
  reviewed version for annual income after an employment ended, without
  reopening it or changing monthly payroll. The annual company and
  pension-consistency checks still run after it. OCA engine only.
  Contributed by votrelec (cssk-public#51).

[19.0.1.26.1] — 2026-11-17
==========================

Added
~~~~~

* ``_l10n_sk_monthly_cash_wage(contract)``: a cooperative hook for the
  monthly wage BASIC is computed from, defaulting to the contract wage. An
  integration can supply a payslip-specific monthly amount without editing the
  contract; absence proration, insurance and tax follow it, hourly pay does not
  use it. The probable-earnings fallback of the § 134 ods. 3 average follows
  the same amount, so holiday and obstacle pay keep GROSS whole; a quarter with
  enough worked time keeps its historical average. OCA engine only.
  Contributed by votrelec (cssk-public#49).

[19.0.1.26.0] — 2026-11-16
==========================

Fixed
~~~~~

* Apply the ordinary agreement pension OOP before the statutory maximum in
  employee pension/disability and employer pension/disability/reserve rules
  (section 138). Guarantee and accident bases remain unreduced by this OOP.
  A 2026 eligible agreement at 17,100 EUR now uses 16,764 rather than 16,564.
  At the 35% marginal tax rate an old-age DoPC employee pays 8.00 more pension
  insurance, TAXBASE decreases by 8.00, tax withheld by 2.80 and NET by 5.20.
  The corresponding student DoBPS at 19,000 EUR has NET lower by 9.10.

Changed
~~~~~~~

* Update the frozen arithmetic reference for these five disclosed changes only.
  The rest of the native rounding, exemptions, rates and dated parameters stay
  unchanged. Existing posted payslips are not automatically recomputed.

[19.0.1.25.2] — 2026-11-16
==========================

Fixed
~~~~~

* **A guarantee-exempt payslip kept a guarantee base.** Where the employer is
  exempt from guarantee insurance (§ 4 ods. 4 zákona 461/2003) the premium was
  already 0, but the recorded guarantee base was still the capped gross. It is
  now 0, as the exempt health base already was and as Enterprise records it.
  The premium arithmetic is unchanged; only the recorded base differs, on
  payslips computed from now on.
* **A health minimum top-up without a health record was dropped.** When the top-up rule
  was computed but no employee health row was recorded (for example a
  customised structure without the health rule), the evidence was stored
  without that charge. The payslip is now left unrecorded, so declarations
  name it instead of reading an incomplete charge.
* **The support check and the reader now follow the contract the payslip was
  computed on.** Recording is supported only when the contracts the engine
  computes over are exactly one contract of the employee and company, so a
  ``contract_id`` outside the period is unsupported on purpose rather than
  because it happened to compute nothing. The reader also requires the
  recorded profile to describe the contract of the payslip lines
  (which must be ``contract_id`` when set), so the identity (which keeps ``contract_id``,
  empty on API-created payslips) and the profile describe one computation.
  Existing evidence is unaffected: its identity is unchanged, and its profile
  was taken from that same contract.
* A test pins every recorded base to the expression its rule charged on (the
  rule's own variable where the formula has one), and an exemption that zeroes
  a premium to a zero base; a test no longer prints to standard output.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

* Not yet on 18.0 (the recorded fund evidence itself is not ported there).

[19.0.1.25.1] — 2026-11-16
==========================

Changed
~~~~~~~

* The fund-base recorder keeps only what belongs to this engine (capture
  hooks, the stored field, payslip identity and refund pairing) and uses the
  shared recorder in ``l10n_sk_hr_payroll_base`` for the rest, which the
  Enterprise bridge will use too. Nothing user-visible changes: the stored
  evidence is byte-identical and the existing tests are unchanged.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

* Not yet on 18.0 (the recorded fund evidence itself is not ported there).

[19.0.1.25.0] — 2026-11-11
==========================

Added
~~~~~

* Actual signed fund-base/rate/charge capture during payslip calculation with
  an in-process capability; generated evidence cannot be supplied over RPC.
* One shared statutory profile without birth numbers, native refund evidence
  and optional recording for custom structures that emit fund values.
* Frozen original-formula references and reference fixtures independent of the
  optional minimum-wage top-up, alongside native signed/subcent/credit cases.

[19.0.1.24.6] — 2026-11-11
==========================

Fixed
~~~~~

- **Payroll kept the 9.30 € stravné after 1 December 2026.** The 5–12 hour
  domestic stravné is 9.80 € from that date (oznámenie MPSVR SR
  č. 255/2026 Z. z.), the rate the travel orders already use. The meal
  contribution and the meal voucher now read it from December 2026 payroll;
  November keeps 9.30 €. Explicit contractual amounts still take priority.
  Contributed by votrelec (cssk-public#44).

[19.0.1.24.5] — 2026-11-10
==========================

Fixed
~~~~~

- **Updating the module failed with approved leave, and reset company
  settings.** Reloading the starter leave types rewrote ``request_unit``,
  which recomputed approved PN and holiday dates and failed the native
  leave state check, and it overwrote each company's own choices. The
  starter leave types are now installation defaults (``noupdate``); a
  change to existing defaults needs a migration. Contributed by votrelec
  (cssk-public#40). The three leave types in
  ``data/hr_leave_options_data.xml`` had the same problem and are covered
  too, as are both Czech engines and the Enterprise engine.

[19.0.1.24.4] — 2026-11-10
==========================

Fixed
~~~~~

- **Employer sick pay at the end of employment and across the year.** The
  employer stops paying when the employment ends (a PN from 5 to 18 June
  with employment ending on 9 June paid 136 instead of 37). Each PN episode
  uses the terms in force at its onset, so a PN begun in 2025 keeps the
  ten-day employer period and the 2025 daily-base cap in 2026. The daily
  base is cut to four decimals (§ 8 ods. 8 zákona 462/2003) and the
  compensation rounded up to the cent (§ 10 ods. 2). An actual zero after
  termination no longer falls through to the manual inputs. Contributed by
  votrelec (cssk-public#39).

[19.0.1.24.3] — 2026-11-10
==========================

Fixed
~~~~~

- The average's worked time subtracts the separately recorded absence days
  and hours from WORK100, with either leave-sign setting, so a holiday in
  the determining quarter no longer understates the next quarter's rate.
  An unsaved payslip uses its persistent origin in the history search.
  Contributed by votrelec (cssk-public#32).

[19.0.1.24.2] — 2026-11-10
==========================

Fixed
~~~~~

- **Sick pay where there is no sickness insurance.** The salary rule now
  asks the shared ``SICKNESS_COMPENSATION`` applicability, so a pensioner's,
  student's or irregular dohoda gets no employer sick pay, while ordinary
  employment of a pensioner stays insured. The rule comment now says that
  the compensation is income-tax exempt (§ 5 ods. 7 písm. f) zákona
  595/2003). Contributed by votrelec (cssk-public#31).

[19.0.1.24.1] — 2026-11-09
==========================

Fixed
~~~~~

- An hourly-paid employee with approved leave received BASIC for every
  scheduled hour and the separate leave compensation on top. Hourly BASIC
  now removes the absence hours first (§ 116 and § 118 Zákonníka práce).
  The BASIC rule delegates to a cooperative country-level helper,
  ``l10n_sk_basic_salary``, with an optional calendar divisor for dated
  wage segments. Contributed by votrelec (cssk-public#30). Hourly BASIC
  is floored at zero, should inconsistent leave data exceed the scheduled
  hours.

[19.0.1.24.0] — 2026-11-09
==========================

Fixed
~~~~~

- Use actual average hourly earnings after at least 21 worked days OR 168
  worked hours (§ 134 ods. 3), including part-time employees with short days.
- Keep determining-quarter sources inside the payroll company and employment
  start, while retaining wage-version changes within the same employment.
- Net native credit notes against both wage and worked time, so a refunded
  original does not count twice or distort a replacement's average.

Added
~~~~~

- Cooperative hooks for source selection, counted wage and worked time, for
  benefit classification and extensions retaining superseded financial records.
- Regression cases with actual calendars, threshold alternatives, company
  isolation, refunds/replacements and rehire versus wage-version changes.
  Contributed by votrelec (cssk-public#28).

[19.0.1.23.0] — 2026-11-09
==========================

Added
~~~~~

- Read the tax pension fact from the native version in force on 1 January.
  No manually advanced tax year or duplicate evidence field is required;
  the retained taxpayer declaration supplies the fact. FS FAQ 3/7/9 distinguishes a January pension (no monthly
  allowance, including small pensions) from a midyear award (allowance kept).
  Insurance pension type and annual pension amount cannot replace that fact.
  Preserve the native tax base and bands and the existing annual pension
  deduction. Review affected historical payslips through a correction workflow.
- Validate contradictions before salary rules and reconcile the January flag
  with the reviewed annual pension amount before computing RZD. A May award
  rolls into the following January without invalidating December payroll.
- Correct the monthly-allowance statement introduced in 19.0.1.21.0. The
  statutory annual high-income taper and the January pension exclusion are
  different rules. Add regression examples for the declaration checkbox,
  small pensions, midyear awards, disability, foreign pensions and annual consistency.

- Accept the January status declared by a genuine midyear hire on the first
  version, without backdating employment. Reuse it for monthly payroll and RZD;
  exclude genuinely future versions. Validate the payslip's actual structure.
  Contributed by votrelec (cssk-public#24).

Fixed
~~~~~

- A rehired employee whose earlier employment ended before 1 January read
  the January status from that ended employment, so a pensioner rehired
  during the year got the monthly allowance. The first version of the new
  employment now states it, as for a hire, and the reconciliation's
  default pension amount comes from the same version.

[19.0.1.21.1] — 2026-11-08
==========================

Fixed
~~~~~

- **The annual tax reconciliation reads only confirmed payslips of its own
  company.** It took every payslip of the employee that was not cancelled,
  in any company, so draft and waiting calculations and another company's
  payroll entered the annual income, insurance and withheld tax. It now
  reads the payslips the payroll declarations read: confirmed (``done``)
  payslips of the reconciliation's company, by the year their period ends
  in, so a payslip that crosses the year boundary counts once. Contributed
  by votrelec (cssk-public#20).

[19.0.1.21.0] — 2026-11-08
==========================

Fixed
~~~~~

- **The annual tax reconciliation reduces a pensioner's NČZD.** § 11 ods. 6
  ZDP: a taxpayer drawing an old-age, early old-age or service pension (or a
  foreign one of the same kind) at the start of the year gets the
  non-taxable part per taxpayer only as far as it exceeds the pension, 13th
  pension included, and none when the pension is higher. The RZD gave every
  pensioner the full amount, so it refunded tax that was owed. The contract
  version has a new *Pension at 1 January (yearly)* amount; the RZD takes it
  from the version in force on 1 January, shows it, and lets it be
  corrected to what the employee declared. The monthly advances are
  unchanged in that release. The claim that January pensioners receive the
  full monthly allowance was incorrect; see the 19.0.1.21.1 correction above.

[19.0.1.20.0] — 2026-11-06
==========================

**Added**

- **Dated parameters from January 2027.** Twelve values follow the 2027
  reference amounts: the social-insurance maximum base 17 820 (11 × the 2025
  average wage of 1 620), the health minimum base 295.22, the NČZD of
  516.64 a month and 6 199.62 a year with its taper (threshold 27 101.20,
  constant 15 233.35), the monthly and annual tax bands, the child-bonus
  taper threshold 29 160, the minimum hourly wage 5.586, the maximum
  nemocenské DVZ 106.5206, and the seasonal-work OOP under § 138b of
  461/2003, which rises from 762 to 810. Payslips and annual reconciliations
  before 2027 keep their 2026 values. The derivation of each figure is in
  the comment above the records. Contributed by votrelec (cssk-public#17).

[19.0.1.19.4] — 2026-11-05
==========================

**Fixed**

- **Agreement OOP from January 2027.** § 138a z. 461/2003, as amended by
  158/2026 Z. z., raises the odvodová odpočítateľná položka for pensioners
  and students on agreements from EUR 200 to EUR 300 a month. Payslips from
  January 2027 used EUR 200, leaving up to EUR 100 a month assessed for
  pension insurance and the reserve fund. Earlier periods keep EUR 200.
  Contributed by votrelec (cssk-public#13).

[19.0.1.19.3] — 2026-11-05
==========================

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.19.2] — 2026-10-31
==========================

**Fixed**

- **Salary rules and categories are shared by every company.** They took
  the company of whoever installed the module, so the Slovak payroll
  structures showed no rules in any other company and could not compute a
  payslip there. The structures were already company-less; the rules now
  are too, and upgrading the module repairs an existing database.

[19.0.1.19.1] — 2026-10-27
==========================

**Fixed**

- **Payslip lines, inputs and worked days are confined to your companies.**
  OCA payroll restricts payslips to the user's companies but not what hangs
  off them, so a payroll user of one company could read another company's
  payslip lines — wages and deductions — from the *Payslip Lines* list, a
  report or an export.

**Changed**

- **Slovak translation.** Time-off types, rule parameters and labels added since the last translation pass showed in English; they are translated now.

[19.0.1.19.0] — 2026-10-27
==========================

**Fixed**

- **Pensioners.** New field *Pension granted (SK)* on the employee / contract (starobný, predčasný starobný, invalidný over or up to 70 %, invalidný at pension age, výsluhový at pension age, invalidný výsluhový). Per zákon 461/2003: a DoVP/DoPČ holder with any of them pays no sickness or unemployment insurance and gets no employer sick pay (§ 4 ods. 1 písm. b)); a starobný, predčasný starobný or over-70 % invalidný pensioner pays no unemployment insurance on any form (§ 19 ods. 3 písm. b)); after a starobný, predčasný starobný or a výsluhový dôchodok at pension age neither the employee nor the employer pays disability insurance (§ 128 ods. 3). Until now every pensioner was charged the full set. Set the field on existing pensioners; payslips already validated are not recomputed.
- **Short-time work contribution only for a pracovný pomer** (§ 128 ods. 1 písm. g)). A dohoda with a regular income was charged 0.5 % of it; the employer instead pays unemployment insurance at 1 % rather than 0.5 % (§ 136 písm. b) bod 2, new dated parameter *Unemployment insurance rate (employer, no short-time financing)*). The employer's total is unchanged; the split between the two funds — and so the výkaz — is now right.
- **One annual tax reconciliation per employee and year is enforced again.** The unique key was declared in a form Odoo 19 ignores, so it never existed. The upgrade deletes unposted duplicates (keeping the one furthest along, then the latest) and logs any posted duplicates, which it leaves for you to resolve. The same goes for the unique code of a rule parameter.
- **The Slovak fields are on the employee form.** They were placed on the contract-template form only, so an employee's tax declaration, children, agreement type and the rest could not be entered. They now sit in the employee's *Payroll* tab, together with *Hourly Wage (SK)*, which no form showed.
- The help of *Guarantee-insurance exempt* cites § 4 ods. 4 zákona 461/2003 (it said § 102).
- A payslip created without a contract (through the API or an import) now computes the hourly rate and the calendar-based figures from the contract the engine computes on. OCA payroll fills the payslip's contract only in the form and the batch wizard.

**Added**

- *Payroll → Configuration → Rule Parameters*: the dated statutory rates and ceilings, which had no screen.
- **Minimum hourly wage on a dohoda.** A new *Agreement Wage Warning* appears on a dohoda whose hourly rate is below the minimum hourly wage in force today (§ 119 ods. 1 extended to dohody by § 223 ods. 2 Zákonníka práce). A warning only.

[19.0.1.18.4] — 2026-10-27
==========================

**Fixed**

- **Annual non-taxable part for 2026** (ročné zúčtovanie): above 26 083,13 € it is now 14 661,11 € (51,6 × ŽM 284,13) less **one third** of the tax base, as § 11 ods. 2 písm. b) ZDP reads from 1. 1. 2026; it was the 2025 shape (a quarter of the base), which gave too high an NČZD up to a base of 49 950 €. 2024 and 2025 keep the quarter (new dated parameter *NČZD taper divisor*).
- 2026 annual tax bands are the ŽM multiples of § 15 (43 983,32 / 60 349,21 / 75 010,32 €), not the rounded monthly ceilings × 12.
- **Child tax bonus taper per child** (§ 33 ods. 11): above the threshold 1/10 of the excess is now taken from EACH child's bonus, monthly and in the annual reconciliation; it used to be taken once from the family total, so families with two or more children received too much.
- **Health minimum preddavok** (§ 16a zákona 580/2004): no top-up for a ZŤP employee or a DoBPŠ student; the minimum is reduced pro rata for PN days and for days outside the contract; each component is rounded down to the cent.
- **Annual leave no longer lapses.** The statutory dovolenka accrual plans — the monthly ones and the archived full-grant-on-1-January ones — forfeited carried-over leave after one year; § 113 Zákonníka práce has no forfeiture, so the validity window is removed. The upgrade clears the pending expiry date on existing allocations of these plans. Days that already lapsed are not restored automatically — check them.
- The help of *Meal Allowance Type* states § 152 ods. 3 correctly: at least 55 % of the meal price, at most 55 % of the 5–12 h stravné per meal (it said "at least 55 % of the statutory meal allowance").

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


[19.0.1.24.3] — 2026-11-10
--------------------------

Fixed
~~~~~

- Stop employer PN compensation at employment end, keep the illness-onset
  limits and daily cap across a year boundary, and round compensation upward.
