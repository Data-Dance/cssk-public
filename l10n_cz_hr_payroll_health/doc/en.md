---
title: CZ Health Insurance Filings (PPPZ, HOZ)
summary: The two employer filings to Czech health insurers — the monthly přehled o platbě pojistného (PPPZ) summed from the payslips, and the hromadné oznámení zaměstnavatele (HOZ) of employees joining and leaving — as XML per insurer.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

A Czech employer reports to **each health insurer** whose clients it employs:

- **PPPZ** — *přehled o platbě pojistného zaměstnavatele*, every month: how
  many of its employees the insurer covers, the sum of their assessment bases
  and the total premium;
- **HOZ** — *hromadné oznámení zaměstnavatele*: which employees joined or
  left.

This module builds both as XML in the common structure the insurers publish
(`PrehledPlatbyZamestnavatele` and `hromadneOznameniZamestnavatele`, version
8 of 2025, whose fixed header reads *2026+*), checked against the shipped
`PPPZ_2025_v8.xsd` and `HOZ_2025_v8.xsd`. One filing goes to one insurer;
file one per insurer. The PPPZ reads payslips through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Czech payroll engine — see
[the Czech payroll guide](module:l10n_cz_hr_payroll_base#declarations).

Unlike the social insurance reports, these two filings were **not** replaced
by the JMHZ in 2026; they still go to the insurers.

## Legal background {#legal}

- **Premium.** Health insurance is 13.5 % of the assessment base, rounded up
  to whole koruny ([§ 2 of the Health Insurance Premium Act](law:cz/1992/592));
  the employee bears one third and the employer two thirds
  ([§ 9 odst. 2 of the Public Health Insurance Act](law:cz/1997/48); in the
  payroll module 4.5 % and 9 %). The employer's premium for a month
  is due from the 1st to the 20th of the following month (§ 5 odst. 2).
- **PPPZ.** By the day the premium is due, the employer gives each insurer
  that covers its employees an overview with the sum of their assessment
  bases, the total premium and the number of employees
  ([§ 25 odst. 3](law:cz/1992/592)). New facts affecting a filed overview are
  reported within 8 days in a corrective overview (*opravný přehled*,
  § 25 odst. 4). Both may be filed only electronically, in the format the
  insurer sets (§ 25 odst. 7).
- **HOZ.** The employer notifies the insurer within 8 days that an employee
  started or ended employment; for someone working only on a *dohoda o
  provedení práce* or *dohoda o pracovní činnosti*, by the 20th of the month
  after they became or stopped being a premium payer
  ([§ 10 odst. 1 písm. a) of the Public Health Insurance Act](law:cz/1997/48)).
  The notification carries the name, surname, permanent address and birth
  number (§ 10 odst. 1, last sentence) and is filed only electronically
  (§ 10c).

## Setting it up {#setup}

On the company form, tab *Payroll Reporting*, group *Health insurance
(PPPZ / HOZ)*, and the company's address:

| Value | Used as |
|---|---|
| *Default health insurer* | the insurer of every employee who has none set; preselected on new filings. Defaults to *111 — VZP*. |
| *Health payer number*, 10 digits | `identifikacniCisloPlatce`, the employer's number at the insurer. Left empty, it is taken as the IČO followed by `00` (the first payroll office). |
| *Company ID* (IČO) | the fallback for the payer number |
| street, city, ZIP, phone | the employer's address (city and ZIP required). The house number is the number at the end of the street; the second street line counts only when it holds nothing but a number. |

Per employee: *Health insurer* (one of 111, 201, 205, 207, 209, 211, 213),
next to *Identification No* on the employee form, the birth number in
*Identification No* (for the HOZ), the private address, and the contract
dates. Until the employee's insurer is set, the employee is reported to the
company's default insurer.

## Monthly overview (PPPZ) {#pppz}

*Payroll Declarations → CZ PPPZ (health)*, then *New*.

1. Choose the **Health insurer**, the **Year** and the **Month**.
2. Leave **Correction Type** on *Regular*, or choose *Corrective* for a
   corrective overview. A corrective overview can be generated only when a
   submitted overview to the same insurer, for the same company, year and
   month exists.
3. Click **Generate**. The module takes the month's confirmed payslips
   (those whose period ends in the month) of the employees who belong to that
   insurer, validates the XML and attaches it.
4. Upload the XML to the insurer's portal and click **Mark Submitted**.

| Item | Taken from |
|---|---|
| number of employees (`pocetZamestnancu`) | employees of that insurer with a non-zero health premium in the month |
| total premium (`soucetPojistneho`) | the sum of the employee and employer health insurance lines (`HEALTHEE`, `HEALTHER`), rounded once |
| sum of assessment bases (`soucetZakladuPojistneho`) | **derived**: that premium divided by 0.135. This also brings in the minimum assessment base, because the payroll charges the shortfall to the employee. |
| type (`typPrehledu`) | *radny* or *opravny* from the correction type |

Generation stops if the insurer is missing, the company has no payer number
(nor IČO), city or ZIP, there are no payslips, or none of them carries a
health premium for that insurer.

## Joiners and leavers (HOZ) {#hoz}

*Payroll Declarations → CZ HOZ (health registration)*, then *New*.

1. Choose the **Health insurer** and the **Event Type** — *Enrol (P)* or
   *Terminate (O)*. It applies to every employee in the notification.
2. Optionally set the **Event Date**; otherwise each employee's contract start
   (enrol) or end (terminate) date is used.
3. Add the **Employees** and click **Generate**.

Each employee becomes a `zmenaZamestance` with the code *P* or *O*, the date,
the birth number as the insured person's number, the name (the last word as
the surname, the rest as the first name) and, where filled in, the private
street, city and 5-digit ZIP. Generation stops for an employee without a 9-
or 10-digit birth number or without the date the event needs.

## Limitations {#limitations}

- **Rounding.** The PPPZ rounds the company's total once; the law rounds each
  employee's premium up. The base is computed back from the premium and can
  differ by a few koruny from the sum of the employees' bases. Compare with
  the payroll recapitulation.
- **Derived base for special cases.** For an employee for whom the state also
  pays premium, or who is exempt from the minimum base, premium ÷ 13.5 % need
  not equal the assessment base. Check those employees.
- The *Correction Reference* field is not written into the XML.
- **HOZ codes.** Only *P* and *O*. Change of insurer, state-insured status,
  first registration of foreigners and corrections are not modelled, and an
  employee without a Czech birth number cannot be notified.
- **HOZ dates** come from the contract current today.
- **Insurers.** Seven insurer codes are shipped; another code needs a code
  change.
- The form version is preselected by today's date, and only version 8 is
  shipped.
- Schema validation checks the shape of the file, not the figures. No filing
  from this module has been confirmed by a live submission.
