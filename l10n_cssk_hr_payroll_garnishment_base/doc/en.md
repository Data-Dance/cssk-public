---
title: CZ/SK Wage Garnishments
summary: A register of Czech and Slovak wage-garnishment orders, the statutory waterfall across all of an employee's orders on the payslip, the employer's notices to the court or bailiff, and remitting the deductions to the payee.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

When a court, a bailiff or an authority orders that part of an employee's
wage be withheld — a Czech *exekuce srážkami ze mzdy*, a Slovak *exekúcia
zrážkami zo mzdy* — the employer becomes the *plátce mzdy* / *platiteľ mzdy*.
It must rank the orders, keep the protected part of the wage untouched,
divide the rest between the creditors in the order the law sets, pay the
money out and account for it.

This module is the **register** for that work:

- one record per order served on you, with its rank, its class and the
  remaining debt;
- a calculation that takes **all** of an employee's running orders at once
  and decides how much each one gets from the month's net wage, under Czech
  or Slovak rules depending on the company's country;
- one **deduction** record per order and payslip, showing which third the
  money came from;
- the employer's **notices** and the **account of deductions**
  (*vyúčtování srážek* / *vyúčtovanie zrážok*) as printouts.

It depends only on Odoo's `hr`, so it has no payroll of its own. The payslip
side comes from the add-ons described under [Payroll engines](#engines), and
the payment to the bailiff from the one under
[Remitting to the payee](#accounting). The family:

| Module | What it does |
|---|---|
| [module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base) (this module) | The register, the calculation, the notices. |
| [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | Ties it to Odoo Enterprise Payroll. |
| [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) | Ties it to the OCA payroll app. |
| [module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account) | Turns deductions into payables to the bailiff. |

The deduction itself is a salary rule of the national payroll:
[module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee),
[module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca),
[module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) or
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca).

## Legal background {#legal}

Checked against the consolidated texts in force in October 2026.

**Czech Republic** — [občanský soudní řád, §§ 276–302](law:cz/1963/99), and
[nařízení vlády č. 595/2006 Sb.](law:cz/2006/595) (*nařízení o
nezabavitelných částkách*). Orders of a *soudní exekutor* follow the same
rules.

- Deductions are made from the **net wage** (*čistá mzda*): the wage less the
  income tax advance and social and health insurance (§ 277).
- The employee keeps the **nezabavitelná částka** (§ 278). Under § 1 of the
  regulation it is 85 % of the sum of the *životní minimum jednotlivce*, the
  *normativní nájemné* for a one-person household in a municipality of at
  least 70 000 inhabitants and the *energetický paušál*, plus one quarter of
  that for each person the employee must maintain. A spouse or partner does
  not count, except where a pension listed in § 1 odst. 2 was granted. The
  amount is rounded up to whole crowns (§ 3), and the figures valid on
  **1 January of the year in which the wage is paid** apply (§ 4).
- The rest (*zbytek čisté mzdy*), rounded down to a sum divisible by three in
  whole crowns, is divided into thirds. An ordinary claim may take one third,
  a priority claim (§ 279 odst. 2 — maintenance, taxes, insurance and others)
  two. Priority claims are paid first from the second third, and only what
  that does not cover competes with the others in the first (§ 279 odst. 1).
- Above **1.9 times** that sum (§ 2 of the regulation) the rest is seized
  without limit; that part joins the second third as far as the priority
  claims need it and the first third otherwise (§ 279 odst. 3).
- When **at least four executions** for money claims are ordered against the
  same wage at once, two thirds are seized: the priority claims are still
  paid from the second third first, but what they leave joins the first
  third instead of staying with the employee (§ 279 odst. 4 and 6). This
  does not apply while the employee has proved an old-age pension, a
  disability pension of the second or third degree or an orphan's pension
  **and** one third stays below the monthly fee and expenses of an
  insolvency trustee (§ 279 odst. 5).
- The first third goes to the claims by rank, priority or not (§ 280
  odst. 1). In the second third, maintenance comes first regardless of rank
  and, when it is not enough, is shared by the current monthly maintenance
  (§ 280 odst. 2 to 4). The rank is the day the order was **delivered to the
  employer**; orders delivered the same day rank equally and share pro rata
  (§ 280 odst. 5).
- The employer starts deducting **from the first day of the calendar month
  following delivery** (§ 282a).
- A new employer that learns of an order must tell the court without delay
  (§ 294 odst. 2). When the debtor leaves, the employer tells the court
  within a week and sends the account of the deductions made, the claims and
  their rank (§ 295 odst. 2). It also issues the leaving employee a
  confirmation of the orders (§ 294 odst. 1). It answers the court's
  enquiries (§ 128 o. s. ř.) and the bailiff's (§ 33 odst. 5 exekučního
  řádu).

**Slovakia** — [Exekučný poriadok](law:sk/1995/233)
(§§ 66–92) and [nariadenie vlády č. 268/2006 Z. z.](law:sk/2006/268)

- Net wage is the wage less the income tax advance and the health, social
  and pension-saving contributions
  ([§ 69 ods. 1](law:sk/1995/233#paragraf-69.odsek-1)).
- The protected **základná suma** depends on what is being collected:
  140 % of the subsistence minimum for an adult for an ordinary claim
  ([§ 1 ods. 1 of the regulation](law:sk/2006/268#paragraf-1.odsek-1)),
  100 % for a priority claim
  ([§ 2 ods. 2](law:sk/2006/268#paragraf-2.odsek-2)), and 70 % of 60 % for
  maintenance of a minor child
  ([§ 2 ods. 1](law:sk/2006/268#paragraf-2.odsek-1) with
  [§ 70 ods. 2 Exekučného poriadku](law:sk/1995/233#paragraf-70.odsek-2)).
  The subsistence minimum valid **in the month for which** the deduction is
  made applies.
- For each maintained person 25 % is added — of the ordinary base, or of the
  100 % base for priority claims
  ([§ 1 ods. 2](law:sk/2006/268#paragraf-1.odsek-2),
  [§ 2 ods. 3](law:sk/2006/268#paragraf-2.odsek-3)). Unlike in the Czech
  Republic, a spouse with an income of their own counts. For a recipient of
  pension benefits the addition is 50 %
  ([§ 2a](law:sk/2006/268#paragraf-2a)).
- Above **three times** the ordinary base the rest is seized without limit
  ([§ 3 ods. 1](law:sk/2006/268#paragraf-3.odsek-1)). The amounts are rounded
  down to the cent ([§ 4](law:sk/2006/268#paragraf-4)).
- Thirds, priority claims and ranking work as in the Czech Republic, in cents
  ([§ 71 ods. 1 and 2](law:sk/1995/233#paragraf-71.odsek-1),
  [§ 72](law:sk/1995/233#paragraf-72.odsek-2)); the rank is the day the
  *príkaz na začatie exekúcie* was delivered
  ([§ 72 ods. 3](law:sk/1995/233#paragraf-72.odsek-3)), and deductions run
  from that day ([§ 66 ods. 1](law:sk/1995/233#paragraf-66.odsek-1)). The
  money is paid to the **exekútor**
  ([§ 81 ods. 1](law:sk/1995/233#paragraf-81.odsek-1)).
- The new employer reports an order it learns of without delay
  ([§ 84 ods. 2](law:sk/1995/233#paragraf-84.odsek-2)); when the debtor
  leaves, the employer notifies the exekútor within a week and sends the
  account of deductions ([§ 85 ods. 2](law:sk/1995/233#paragraf-85.odsek-2)).

## Setting it up {#setup}

1. The company's country must be the Czech Republic or Slovakia. In any
   other company, orders are ignored by payroll.
2. Check the statutory figures under
   *Employees → Configuration → Garnishment Rates* (HR administrators only).
   The shipped values are listed under [Statutory figures](#rates). Add a new
   record, with its *Date From*, when a figure changes.
3. On each employee with an order, tab *Settings*, group
   **Wage Garnishment**:

   | Field | What it does |
   |---|---|
   | Maintained Persons | Persons the employee must maintain. Each raises the protected amount. Decide yourself who counts: the two countries treat a spouse differently (see [Legal background](#legal)), and nobody counts on whose behalf a maintenance execution is running. |
   | Pension Recipient | Slovakia: the employee receives pension benefits, so each maintained person adds 50 % instead of 25 %. Czech Republic: the employee has proved an old-age pension, a disability pension of the second or third degree or an orphan's pension; this lifts the two-thirds rule for four or more executions while one third stays below the insolvency trustee's monthly amount (§ 279 odst. 5 o. s. ř.). |

   The national payroll modules have their own *Garnishment Dependents*
   field on the contract for the older single-claim rule. When *Maintained
   Persons* is left at 0, the register uses that contract field (the
   contract valid at the end of the period); a number entered here always
   wins.

Access: HR officers (*Officer: Manage all employees*) see and edit orders
and deductions; deleting them needs the HR *Administrator*. The records are scoped to
the company, and payslips only ever use orders of their own company.

## Registering an order {#orders}

*Employees → Garnishments → Orders*, *New*.

| Field | Meaning |
|---|---|
| Case Number | The *spisová značka* / *číslo konania*, e.g. `123 EX 456/2026`. |
| Employee | The debtor. |
| Type | *Court execution*, *Insolvency*, *Agreement* (*dohoda o srážkách ze mzdy*) or *Administrative enforcement*. In a Czech company it decides whether the order counts towards the four executions of § 279 odst. 4 o. s. ř.: *Court execution* and *Administrative enforcement* count, *Agreement* and *Insolvency* do not. Otherwise it does not change the calculation. |
| Claim Class | **What drives the calculation.** *Maintenance (výživné)*, *Priority*, *Ordinary*, and in Slovakia also *Administrative fine*. Take it from the order. For a Czech insolvency (*oddlužení*), where deductions run as for priority claims, choose *Priority*. |
| Delivered On | The day the order reached **you**. This sets the rank. |
| Date Start / Date End | The period the order applies to. *Date Start* defaults, for a Czech company, to the **first day of the month after delivery** (§ 282a o. s. ř.), and for a Slovak company to the delivery date. It can be changed; a manual value is kept until *Delivered On* changes. |
| Total Claim | Principal, costs and interest from the order. Leave 0 for open-ended current maintenance. |
| Monthly Maintenance | The current monthly maintenance. With no total, the order is open-ended and never settles by itself. |
| Arrears | Maintenance already overdue, collected on top of the monthly amount (shown for maintenance only). |
| Creditor, Bailiff | The *oprávněný* and the *soudní exekutor* / *súdny exekútor*. When a bailiff is set, the money goes to the bailiff. |
| Payee, Payee Bank Account | Who is paid (computed) and into which of the payee's accounts. An account belonging to someone else is refused. |
| Variable Symbol | The digits of the case number, last 10; editable. Specific and constant symbol as the order asks. |

An order needs a total claim or a monthly amount. Attach the order itself on
the *Document* tab.

**Statuses.** *Draft* orders are ignored by payroll. **Start** puts the order
into *Running* — only running orders are deducted. **Suspend** pauses it
(e.g. a postponement), **Mark Settled** closes it, **Cancel** withdraws it,
**Reset to Draft** reopens a suspended or cancelled one. An order whose total
has been deducted in full closes itself when the payslip that pays it off is
confirmed; cancelling or resetting that payslip reopens it.

The employee form shows a **Garnishments** button with the number of running
orders.

## On the payslip {#payslip}

The national payroll's **Wage Garnishment** rule (`GARNISHMENT`) runs after
tax and insurance. If the employee has a running order of the payslip's
company, the register computes the deduction from the payslip's net wage over
all running orders whose period overlaps the payslip, and the rule deducts
the total.

Nothing is written to the orders while the payslip is a draft, however often
it is recomputed. When you **Confirm** the payslip, one deduction per order
is recorded from the same net wage, and the payslip shows them on a
**Garnishments** tab. You find them all under
*Employees → Garnishments → Deductions*.

- **Cancel** or **Set to Draft** on the payslip deletes its deductions that
  have not been remitted.
- A payslip whose deduction has already been **remitted** can be neither
  cancelled nor set back to draft; reverse the remittance first.
- Employees with no registered order keep the older input-driven rule of the
  national payroll, so you can move to the register one employee at a time.

## How the deduction is computed {#calculation}

**Czech Republic**, in whole crowns:

1. Protected amount = 85 % × (subsistence minimum + normative rent + energy
   allowance) × (1 + ¼ × maintained persons), rounded up.
2. Remainder = net wage − protected amount. Up to the limit it is rounded
   down to a multiple of three and split into thirds; above the limit it is
   seized in full.
3. **Second third**: maintenance first, regardless of rank, shared by the
   current monthly maintenance if it is not enough; then the other priority
   claims by rank. What priority claims do not use stays with the employee —
   unless the two-thirds rule applies (step 6).
4. **First third**: everything still unpaid — priority and ordinary — by
   rank; equal rank shares in proportion to what is owed.
5. The fully seizable part above the limit is added to the second third as
   far as priority claims need it, the rest to the first third.
6. **Four or more executions** (§ 279 odst. 4–6): when at least four running
   orders of the employee are of type *Court execution* or *Administrative
   enforcement*, what the priority claims leave of the second third is added
   to the first third and shared by all claims by rank. Not when the
   employee is marked *Pension Recipient* and one third is below the
   *Insolvency trustee monthly amount* (§ 279 odst. 5).

Example (2026): net wage 30 000 Kč, one maintained child, one ordinary
order. Protected amount 14 101.50 + 3 525.375 = 17 626.875 → **17 627 Kč**.
Remainder 12 373 → 12 372, third **4 124 Kč** — the ordinary order gets
4 124 Kč, the employee 25 876 Kč.

**Slovakia**, in cents: the same waterfall, but the protected base depends on
the claim class (140 %, 100 %, 70 % × 60 % or 50 % of the subsistence
minimum). The module computes the thirds separately for each class present,
lets priority claims take their second third and the part above the limit,
and lets the unpaid rest compete in the first third. Two safeguards keep it
conservative: no order gets more than its own class would allow on its own,
and the employee always keeps at least the smallest protected base among the
orders actually deducted. Where they trim an order, the money stays with the
employee.

## Statutory figures {#rates}

| Country | Valid from | Figures |
|---|---|---|
| CZ | 1 Jan 2026 | subsistence minimum 4 860 Kč, normative rent 9 430 Kč, energy allowance 2 300 Kč (sum 16 590 Kč); 85 %; ¼ per person; unlimited above 31 521 Kč (1.9 × 16 590); insolvency trustee monthly amount 1 089 Kč ((750 + 150) × 1.21, vyhl. 313/2007 Sb.) |
| SK | 1 Jul 2024 | subsistence minimum 273.99 € |
| SK | 1 Jul 2025 | subsistence minimum 284.13 € |
| SK | 1 Jul 2026 | subsistence minimum 295.22 € |

The Slovak coefficients are the same in every record: ordinary 140 %,
priority 100 %, maintenance of a minor 70 % × 60 %, fine 50 %, 25 % per
person (50 % for a pension recipient), unlimited above 3 × the ordinary base.
For 2026/27 that is a protected base of 413.30 € (295.22 € × 140 % =
413.308 €, rounded down).

No Czech record before 2026 is shipped: the 2026 reform changed the formula
itself. From 1 October 2026 the Czech subsistence minimum for an individual
is 5 500 Kč, but § 4 of the regulation keeps the 1 January value for wages
paid in 2026; add a 2027 record before computing wages paid in 2027.

## Notices and the account of deductions {#notices}

*Employees → Garnishments → Statutory Notices* prints, for one employee and
some or all of their orders:

| Notice Type | Contents |
|---|---|
| Notice of employment start | the debtor joined on the *Event Date*; the orders on file |
| Notice of employment end | the debtor left on the *Event Date*; the state of each order |
| Answer to an enquiry | the orders in their rank with the claim, the amount deducted and the remainder |
| Account of deductions (*vyúčtování srážek*) | the orders and every deduction in the period, split into second and first third, with the remitted status |

*Addressee* defaults to the payee of the first selected order. The printouts
are in English with the Czech title and are signed by hand. Under the title
the notice cites the provision of the company's country:

| Notice Type | Czech company | Slovak company |
|---|---|---|
| Notice of employment start | § 294 odst. 2 o. s. ř. | § 84 ods. 2 Exekučného poriadku |
| Notice of employment end | § 295 odst. 2 o. s. ř. | § 85 ods. 2 Exekučného poriadku |
| Answer to an enquiry | § 128 o. s. ř. / § 33 odst. 5 exekučního řádu | *Odpoveď na žiadosť exekútora* (no paragraph) |

## Payroll engines {#engines}

Two bridges connect the register to a payroll application. Each installs
itself when its engine and this module are both installed:

| | Enterprise | OCA |
|---|---|---|
| Module | [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) |
| Payroll app | Odoo Enterprise *Payroll* (`hr_payroll`) | OCA `payroll` |

They do the same thing: record the deductions when a payslip is confirmed,
delete them when it is cancelled or set to draft, refuse to cancel or reset
a payslip whose deduction was remitted, and add the *Garnishments* tab to the
payslip. The amount on the payslip needs only this module and the national
salary rule; without a bridge nothing would be recorded per order and orders
would never settle.

## Remitting to the payee {#accounting}

[module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account)
installs itself together with `account` and
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols).

The payroll entry credits one collective liability for all garnishments
(e.g. 379). Remitting moves each order's share onto the payee:

    Dr  garnishment liability (collective)
        Cr  payable of the bailiff or creditor (partner set)

one posted entry per order, with the order's variable, specific and constant
symbols and its payee bank account. The open payable is then paid like any
supplier — by a payment order and bank file, or matched on the bank
statement.

1. *Accounting → Configuration → Settings* (on Community without full
   accounting *Invoicing → Configuration → Settings*), block
   **Wage Garnishments**: choose the **Garnishment Remittance Journal** (a
   miscellaneous journal) and the **Garnishment Liability Account** — the
   same account the payroll posting credits for garnishments.
2. The payee needs an *Account Payable*.
3. Either *Employees → Garnishments → Remit to Payees*: choose *Up To* and
   optionally *Only This Payee*, check the list and click **Remit**; or
   select deductions under *Deductions* and click **Remit to Payee**.

The entry is dated with the last period end it covers. Remitted deductions
show *Remitted* and cannot be deleted. The menu and the button are shown to
the Accounting *Administrator* and to users in the group *Show Full
Accounting Features*, and the menu sits under *Employees*, so it also needs
an HR role. An accountant can change nothing on a deduction except its
remittance.

## Limitations {#limitations}

- **Czech orders registered before version 19.0.1.2.2** keep the *Date
  Start* stored then — the delivery date. Move it to the first day of the
  following month on any order whose delivery month has not been paid yet.
- **Czech year of payment.** The figures are those valid on 1 January of the
  year in which the wage is **paid** (§ 4 of the regulation). The payment
  date is taken from the payslip when the payroll engine records one
  (Enterprise *Payment Date*, once the payslip is paid); otherwise the wage
  is assumed to be paid in the month after the period, the latest the Labour
  Code allows. A wage paid within its own month across a year end — a
  December wage paid in December — therefore uses the following year's
  figures on the OCA engine.
- **Employer's flat-rate fee.** The *paušální náhrada nákladů plátce mzdy*
  (50 Kč a month, CZ § 279 odst. 1 o. s. ř. with § 4d–4e of vyhláška
  č. 485/2000 Sb.) is not computed or withheld. The employer may waive it;
  if you claim it, deduct it outside the register.
- **Slovak rounding** follows § 4 of the regulation: the protected sums and
  the unlimited limit are rounded down to the cent. The debtor's sum and the
  per-person sum are rounded separately (413.30 € + 103.32 € per person for
  2026/27), which is how the paragraphs define them; rounding only their
  total could protect a cent more.
- **Slovak fines.** *Administrative fine* uses 50 % of the subsistence
  minimum plus 25 % per person. That base, § 2b of the regulation, concerns
  fines collected from benefits otherwise exempt from execution and adds
  nothing per person; check before using this class for a wage.
- **The Slovak mixed-class waterfall** is a modelling choice where the law
  is silent; with orders of different classes, have the result checked.
- **Notice language.** The printouts are in English with the Czech title
  also for Slovak companies, and there is no printout of the leaving
  employee's confirmation (§ 294 odst. 1, SK § 84 ods. 1).
- **Only wages.** Sickness benefits, pensions and other income paid by third
  parties are out of scope, as are court-approved reduced deductions
  (§ 287 / SK § 77) and arrears of wages for several months (each month must
  be computed separately).
- The *From Unlimited Part* of a deduction is not tracked; the part above
  the limit is counted in the thirds.
- The statutory notices to the exekútor about long sick leave or maternity
  leave (SK § 67 ods. 4 and 5) are not produced.
