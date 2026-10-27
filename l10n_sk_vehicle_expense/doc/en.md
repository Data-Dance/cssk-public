---
title: SK Vehicles and Fuel — VAT and Income-Tax Flat Rates
summary: The 50 % VAT deduction on passenger vehicles used also privately (§ 85n) as purchase taxes, and the 80 % fuel flat rate for income tax as a split on the vendor bill — two independent Slovak regimes.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

A passenger car used for business and private purposes is restricted
twice, and since 1 January 2026 the two restrictions are independent of each
other:

| Regime | Rule | Share | How this module handles it |
|---|---|---|---|
| VAT deduction (*odpočet DPH*) | § 85n of the VAT Act | **50 %** of the VAT on the vehicle and everything bought for it | two purchase taxes that deduct only half the VAT — see [VAT](#vat) |
| Fuel as an income-tax expense (*daňový výdavok na PHL*) | § 19 ods. 2 písm. l) bod 3 of the Income Tax Act | flat rate up to **80 %** of fuel bought | a wizard on the vendor bill that moves the rest to a non-deductible account — see [Fuel split](#fuel) |

Each half can be used without the other: the VAT taxes on a repair bill,
the fuel split on a fuel bill of a company that is not a VAT payer, both on
the fuel bill of a VAT payer.

## Legal background {#legal}

**VAT.** [§ 85n of the VAT Act](law:sk/2004/222#paragraf-85n) applies from
1 January 2026 to 30 June 2028 to motor vehicles of categories **M1, L1e and
L3e** (*osobné motorové vozidlo*):

- a payer that acquires such a vehicle as a long-term asset deducts the VAT
  on it at **50 %**
  ([ods. 1](law:sk/2004/222#paragraf-85n.odsek-1)); the same applies to the
  VAT on a lease other than a short-term one
  ([ods. 2](law:sk/2004/222#paragraf-85n.odsek-2)) and to goods and
  services received in connection with a vehicle used for business as well
  as other purposes — fuel, repairs, vignettes and the like
  ([ods. 3](law:sk/2004/222#paragraf-85n.odsek-3));
- the limit does not apply to vehicles used exclusively for short- or
  long-term rental, carriage of passengers including taxi, driving schools,
  or as demonstration or replacement vehicles
  ([ods. 4](law:sk/2004/222#paragraf-85n.odsek-4)), nor to a vehicle used
  exclusively for business when the payer keeps detailed **electronic
  records** of every trip
  ([ods. 5](law:sk/2004/222#paragraf-85n.odsek-5) and
  [ods. 6](law:sk/2004/222#paragraf-85n.odsek-6));
- the use under ods. 4 or 5 must be **notified** to the tax office on the
  Finančné riaditeľstvo's form by the deadline of the return in which the
  deduction is first claimed
  ([ods. 9](law:sk/2004/222#paragraf-85n.odsek-9)).

Until 31 December 2025 the last part of
[§ 49 ods. 5](law:sk/2004/222#paragraf-49.odsek-5) let a payer who claimed
the fuel flat rate for income tax and could not prove the business share
deduct VAT on fuel up to that flat rate. That clause is gone from 1 January
2026; the VAT deduction no longer follows the income-tax flat rate.

**Income tax.** Fuel consumed is a tax expense, among other methods, as a
**flat rate up to 80 %** of the total proven fuel purchase for the period,
provided the number of kilometres driven, per the odometer at the start and
end of the period, is reasonable — for each vehicle separately
([§ 19 ods. 2 písm. l) bod 3](law:sk/2003/595#paragraf-19.odsek-2.pismeno-l.bod-3)).
It is one of four methods the provision allows; choosing it is the
taxpayer's decision.

**The VAT that is not deducted.** As a rule the Income Tax Act counts VAT
the payer has no right to deduct as a tax expense
([§ 19 ods. 3 písm. k) bod 2](law:sk/2003/595#paragraf-19.odsek-3.pismeno-k.bod-2))
and, on tangible assets, as part of the entry price
([§ 25 ods. 5 písm. b)](law:sk/2003/595#paragraf-25.odsek-5.pismeno-b)).
For the VAT that § 85n leaves undeducted, a transitional provision in force
from 1 January 2026 says the opposite:
[§ 52zzzk](law:sk/2003/595#paragraf-52zzzk) — *"Za daňový výdavok podľa § 2
písm. i) a § 19 sa nepovažuje daň z pridanej hodnoty podľa osobitného
predpisu, ak na jej odpočítanie nemá platiteľ dane z pridanej hodnoty nárok,
pričom ak ide o daň z pridanej hodnoty vzťahujúcu sa na hmotný majetok …,
táto nie je súčasťou vstupnej ceny"*, the "osobitný predpis" being § 85n of
the VAT Act. So the non-deducted half is **not a tax expense**, and on a
purchased vehicle it is **not part of its entry price** for tax
depreciation. This module books it on the same account as the
non-deductible share of fuel (see [VAT](#vat)), from which it is added back
in the income-tax return.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Vehicles and fuel**
(*Vozidlá a PHL*), setting **Flat rates** (*Paušály*), shown only for
companies with the Slovak chart. The § 85n share is not among them: the
law fixes it at 50 %, and it is built into the two vehicle taxes.

| Setting | Default | Effect |
|---|---|---|
| Fuel tax-expense share (%) | 80 | The share the fuel split keeps as a tax expense, proposed in the wizard. |
| Non-deductible vehicle costs | 548000 *Ostatné náklady na hospodársku činnosť* | The account the fuel split moves the rest to, proposed in the wizard. |

The two taxes, **23 % vozidlo (50 % odpočet)** and **19 % vozidlo (50 %
odpočet)**, appear in *Accounting → Configuration → Taxes*. They are created
when the module is installed, for every company that already has the Slovak
chart, and when the Slovak chart is loaded into a company later. A tax the
company already has is left as it is. If a company's chart lacks an account
or tax group the taxes need (343120, 343110, 548000, the 23 % or 19 % VAT group), the
installation skips that company and logs a warning; create its taxes by hand,
modelled on the standard purchase taxes, with the tax distribution described
below.

## VAT: the vehicle taxes {#vat}

On a bill for something § 85n covers — the purchase or long-term rental of
the vehicle, fuel, repairs, a vignette — choose **23 % vozidlo (50 %
odpočet)** (or the 19 % one) on the line instead of the ordinary purchase
tax. The supplier's full VAT is still charged and paid; the tax splits it:

| Part of the VAT | Account | Tax grid |
|---|---|---|
| 50 % — deducted | 343120 (23 %), 343110 (19 %) | the same deduction row of the VAT return as the ordinary purchase tax of that rate |
| 50 % — not deducted | 548000 | none: it reaches no row of the return |

Example: fuel for 100.00 plus 23 % VAT. The bill total is 123.00; 11.50 of
VAT is deducted on 343120, 11.50 goes to 548000.

Splitting the VAT in the tax itself is what keeps the return right: only the
deductible half carries the tax grid. Moving half of a fully deductible VAT
to an expense with a journal entry afterwards would still report the full
amount as deducted.

Use the ordinary taxes for vehicles § 85n does not cover — other categories,
the exempt uses of ods. 4, or a vehicle used exclusively for business with
the records of ods. 6.

## Fuel split for income tax {#fuel}

On a vendor bill or refund **in draft**, click **Split fuel** (*Rozúčtovanie
PHL*):

1. *Tax-expense share (%)*: proposed from the settings (80).
2. *Non-deductible account*: proposed from the settings (548000).
3. *Fuel lines*: pick the bill lines that are fuel.
4. Click **Split**.

Each selected line keeps the tax-expense share of its amount; a new
line with the rest is added on the non-deductible account, with the same
taxes. The bill total, the VAT and the payable do not change — only the
expense is reclassified. The chatter records the split.

Example, continued: the 100.00 fuel line becomes 80.00 on the fuel expense
account and 20.00 on 548000, both with the vehicle tax.

A line that has already been split cannot be split again. Splitting
rewrites the line as quantity 1 at the remaining amount (any discount is
already reflected and is cleared). The amount is split as entered: with a
tax that includes the price, the gross price is split, so the bill total
stays the same either way.

## In the tax return {#reporting}

- The VAT return picks up only the deducted half, through the tax grid; no
  further step is needed.
- The amounts on the non-deductible account are **not** transferred to the
  corporate income tax return automatically. Enter them among the add-backs
  of the return yourself — see
  [module:l10n_sk_dppo](module:l10n_sk_dppo#usage). The non-deducted § 85n
  VAT and the non-tax share of fuel both are add-backs (see
  [Legal background](#legal)), as long as nothing else is booked on that
  account.

## Limitations {#limitations}

- Nothing is date-gated. The 50 % regime applies from 1 January 2026 to
  30 June 2028; on bills outside that window choose the tax yourself.
- The module does not know your vehicles: categories M1/L1e/L3e, the exempt
  uses and exclusive business use are not modelled, there is no logbook or
  electronic trip record under § 85n ods. 6, and the notification under
  ods. 9 is not produced.
- The non-deducted VAT always goes to 548000 (the account in the tax), even
  if you change *Non-deductible vehicle costs*. On a vehicle purchase it
  lands in expenses, not in the cost of the asset — right for income tax
  (§ 52zzzk), but whether your accounting should capitalise it is for your
  accountant to decide.
- The new line of a split carries no product, and the original line loses
  its quantity (litres).
- Whether the 80 % flat rate may be used — the reasonable mileage per the
  odometer, vehicle by vehicle — is the accountant's call, not the module's.
