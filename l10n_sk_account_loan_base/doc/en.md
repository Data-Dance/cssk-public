---
title: SK Leasing and Loans (finančný prenájom)
summary: Slovak account defaults for finance leases and loans — 474, 474100, 562 and 022 — applied to whichever loan engine your edition runs.
verified: 19.0.1.0.4
---

## What it is for {#purpose}

A car or machine acquired on a **finance lease** (*finančný prenájom*,
commonly *lízing*) is the lessee's asset from day one: it goes on the asset
account, the lease liability on 474, and each instalment splits into
principal and interest. Odoo can keep the repayment schedule and post the
instalments, but which program does it depends on the edition, and neither
knows the Slovak accounts:

| Edition | Engine | Bridge module |
|---|---|---|
| Community | OCA `account_loan` + `account_leasing` | [module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca) — see [Community](#community) |
| Enterprise | Odoo `account_loans` | [module:l10n_sk_account_loan_ee](module:l10n_sk_account_loan_ee) — see [Enterprise](#enterprise) |

The two engines define the same models differently, so **only one can be
installed**; Odoo refuses the combination.

This module ([module:l10n_sk_account_loan_base](module:l10n_sk_account_loan_base))
holds what is Slovak rather than engine-specific: four company accounts and
the settings screen for them. The bridge for your engine installs itself and
copies those accounts onto every new loan or lease.

Only a finance lease belongs here. An **operating lease** (*operatívny
prenájom*) is not a loan: its rent is a period cost, deferred where needed
with [module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff).

## Legal background {#legal}

- **Accounting at the lessee.** On the day the asset is received, it is
  booked on the asset account at the principal (*istina*) against **474**
  *Záväzky z nájmu*
  ([§ 30a ods. 7 opatrenia 740/2002](law:sk/2002/740#paragraf-30a.odsek-7));
  the interest falling due with each instalment is booked on **562**
  *Úroky* against 474 ([§ 30a ods. 9](law:sk/2002/740#paragraf-30a.odsek-9)),
  and at the balance-sheet date the interest accrued since the last
  instalment is booked as well
  ([§ 30a ods. 10](law:sk/2002/740#paragraf-30a.odsek-10)).
- **Income tax.** A finance lease is the acquisition of tangible property
  under a lease with an agreed right to buy, where ownership passes without
  undue delay after the lease ends and the lease runs for at least **60 % of
  the depreciation period** of § 26 ods. 1 —
  [§ 2 písm. s) of the Income Tax Act](law:sk/2003/595#paragraf-2.pismeno-s).
  The lessee depreciates the asset over the ordinary period of its
  depreciation group ([§ 26 ods. 8](law:sk/2003/595#paragraf-26.odsek-8);
  periods in [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1)).
- **VAT.** Handing over goods under a lease by which ownership "za
  normálnych okolností" passes at the latest with the last instalment is a
  **supply of goods**
  ([§ 8 ods. 1 písm. c) of the VAT Act](law:sk/2004/222#paragraf-8.odsek-1.pismeno-c)):
  the lessor charges VAT once, on the whole price, at handover; the
  instalments that follow carry no further VAT. The words "za normálnych
  okolností" apply from 1 January 2025 and make the economic substance of the
  contract decisive rather than its wording. A lease that is not such a
  supply is a service taxed instalment by instalment.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Finančný prenájom (SK)**,
shown only for companies using the Slovak chart:

| Setting | Default | Used for |
|---|---|---|
| Leasing — long-term liability | 474000 *Záväzky z nájmu* | the part of the liability due after one year |
| Leasing — current portion | 474100 *Lízing (bežná časť)* | the part due within one year; the instalments are posted against it |
| Leasing — interest expense | 562000 *Úroky* | the interest in each instalment |
| Leased asset | 022000 *Samostatné hnuteľné veci a súbory hnuteľných vecí* | the asset account the leased item is capitalised on (Community engine only) |

The accounts are filled when the Slovak chart is loaded and, for companies
that already had it, when the module is installed — only where still empty,
so a choice your accountant has made is never overwritten. They are
defaults: each loan keeps its own copy, which you can change on the loan.

## Community engine (OCA) {#community}

[module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca)
installs itself with OCA `account_leasing`. The OCA screens are in English.

1. *Accounting → Accounting → Loans → Loans*, *New*. Choose the type
   **Leasing**, the lessor as *Lender*, the amount, rate, number of periods
   and period length, and the start date.
2. On a Slovak company the accounts arrive filled in: *Long term account*
   474000, *Short term account* 474100, *Interests account* 562000, and on
   the *Leasing* tab the leased asset account 022000. If you switch the
   company on the form, they are refilled from the new company instead of
   being cleared. Set the *Loan product* and *Interest product* used on the
   instalment bills.
3. **Compute items** builds the schedule. **Post** books the asset: debit
   the leased asset account, credit 474100 with the principal due within a
   year and 474000 with the rest.
4. Generating the entries creates, for each instalment, a vendor bill from
   the lessor — principal on 474100, interest on 562000 — and a transfer of
   the next portion from 474000 to 474100.

**VAT on the instalments.** On a Slovak company the *Leasing* tab has a
group **Slovak tax treatment** with:

- *Režim DPH* (VAT regime) — required on a leasing contract:
  - *Dodanie tovaru* (supply of goods): the bridge removes the VAT from
    every line of the instalment bills, because a lease that is a supply of
    goods has had its VAT charged at handover (see
    [Legal background](#legal)). Book the lessor's handover invoice with the
    full VAT separately as an ordinary vendor bill.
  - *Dodanie služby* (supply of services): the instalment bills keep the
    taxes of the *Loan product* and *Interest product*.
- *Odpisová skupina predmetu* (the depreciation group of the leased item)
  and the lease term in months; when the term is shorter than 60 % of that
  group's period, a warning says the contract is not a finance lease under
  § 2 písm. s). The minimum is rounded up to whole months: 60 % of group 2's
  six years is 43.2 months, so a group 2 lease needs at least 44. Groups 0
  (two years) to 6 are offered.

A new lease starts with no VAT regime, and until one is chosen its
instalment bills keep their taxes: removing VAT is the decision that has to
be taken explicitly.

**Leases created before version 19.0.1.0.3** had *Dodanie tovaru* filled in
by default, because the field was not on the form. Open each of them and
confirm or change the regime; the change applies to instalment bills
generated afterwards.

## Enterprise engine {#enterprise}

[module:l10n_sk_account_loan_ee](module:l10n_sk_account_loan_ee) installs
itself with Odoo Enterprise's `account_loans`.

*Accounting → Accounting → Assets & Liabilities → Loans* (in Slovak
*Majetok a záväzky → Úvery*), *New*. On a Slovak company a new loan opens
with *Long Term Account* 474000, *Short Term Account* 474100 and *Expense
Account* 562000. Enterprise itself copies the accounts of the company's
previous loan when there is one; the bridge fills only what is still empty,
so once you have entered a first loan, its accounts win over the defaults.

Enterprise does not use the leased-asset account: it links a loan to assets
through *Asset Group* and *Linked Assets*. The VAT handling of the Community
bridge does not exist here either; Enterprise loans post journal entries,
not instalment bills.

## Limitations {#limitations}

- On the Enterprise engine the Slovak lease fields (*Režim DPH*, *Odpisová
  skupina predmetu*, the 60 % warning) exist on the loan record but no form
  shows them. They change nothing there, since Enterprise creates no
  instalment bills.
- With *Dodanie tovaru* the VAT is removed from all lines of the instalment
  bills, the interest line included.
- The handover invoice with VAT, the depreciation of the leased asset and
  the year-end accrual of interest (§ 30a ods. 10) are not handled; the
  Community engine debits the asset account directly and creates no asset
  record to depreciate.
- Whether a contract is a finance or an operating lease, and how the
  liability is split into long-term and current parts, is your accountant's
  call; the defaults should be reviewed with them.
