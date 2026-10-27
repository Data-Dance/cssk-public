---
title: CZ/SK Supplier Reliability Check
summary: Before you pay a supplier, checks the tax authority's registers for the supplier's reliability and for the bank account you are paying, and keeps the answer on the bill and the payment as evidence.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

In both countries a VAT payer who buys from a supplier can be made to pay the
supplier's unpaid VAT — *ručenie za daň* in Slovakia, *ručení za nezaplacenou
daň* in the Czech Republic. Two of the circumstances that trigger it can be
checked in public registers before you pay:

- whether the supplier is flagged by the tax authority (CZ: **nespolehlivý
  plátce**; SK: on the list of payers with grounds for cancelling the
  registration);
- whether the bank account you are paying is one the supplier has **published
  with the tax authority**.

This module asks those registers when a vendor bill or a supplier payment is
posted, writes the answer onto the document with a timestamp, and shows a
warning when there is a risk. It **never blocks** posting or paying: the
decision stays with you, and the record shows what the register said at the
time.

The module itself holds no register connection. The lookups come from a
country provider:

| Supplier | Provider | Register |
|---|---|---|
| Czech | [module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) | Ministry of Finance ADIS web service (*registr plátců DPH*) |
| Slovak | [module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability) | Financial Administration open data |

Without a provider for the supplier's country every check comes back
*Not checked / unavailable*, without a warning.

## Legal background {#legal}

**Slovakia** — [zákon o DPH](law:sk/2004/222):

- Under [§ 69 ods. 13](law:sk/2004/222#paragraf-69.odsek-13) the platiteľ who
  receives a supply is liable (*ručí*) for the VAT on the supplier's invoice
  that the supplier did not pay, if it knew or should have known that the tax
  would not be paid.
  [Písm. c)](law:sk/2004/222#paragraf-69.odsek-13.pismeno-c) names, as a
  sufficient reason, paying to an account other than the supplier's account
  that was **published on the day of payment** in the list of bank accounts;
  the day of payment is the day you gave your bank the payment order.
- The list itself is published under
  [§ 6 ods. 6](law:sk/2004/222#paragraf-6.odsek-6).
- [§ 69 ods. 14](law:sk/2004/222#paragraf-69.odsek-14) has the Financial
  Directorate publish the payers for whom grounds for cancelling the
  registration under § 81 ods. 3 písm. b) second point arose (repeated failure
  to file or pay, not reachable at the registered address, and similar).
- The liability itself is enforced under
  [§ 69b](law:sk/2004/222#paragraf-69b);
  [§ 69c](law:sk/2004/222#paragraf-69c) lets the customer pay the VAT from the
  invoice directly to the tax administrator's account kept for the supplier
  (*osobitný spôsob úhrady dane*).
- The **index daňovej spoľahlivosti** (highly reliable / reliable / less
  reliable) is set under
  [§ 53d of the daňový poriadok](law:sk/2009/563#paragraf-53d) and published
  under [§ 52 ods. 17](law:sk/2009/563#paragraf-52.odsek-17). It is not one of
  the § 69 ods. 13 reasons; the module shows it as additional information.

**Czech Republic** — [zákon o DPH, § 106a, § 109, § 109a](law:cz/2004/235):

- § 106a: the tax administrator decides that a payer who seriously breaches
  its obligations is a **nespolehlivý plátce**.
- § 109 odst. 2: the recipient is presumed to have known that the tax would
  not be paid — and is liable for it — among other cases when the supplier is
  published as a nespolehlivý plátce (písm. a)), or when the payment goes by
  bank transfer to an account **other than the supplier's account published by
  the tax administrator** (písm. c) bod 2).
- § 98 písm. d): the published accounts are those the payer named for
  publication in its registration.
- § 109a: the recipient can pay the supplier's VAT directly to the supplier's
  tax administrator (*zvláštní způsob zajištění daně*).

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Vendor Bills**, setting
**Supplier reliability check (CZ/SK)**. It is on by default for every company;
switch it off per company if you only want to check by hand.

The check runs only for companies whose fiscal country is Slovakia or the
Czech Republic. Install the provider for each country your suppliers come
from; the Slovak one also needs an API key (see [below](#sk-provider)).

The supplier needs the identifier the register searches by:

| Supplier | Needed on the contact |
|---|---|
| Czech | country Czech Republic and *Tax ID* (`CZ12345678`) |
| Slovak | country Slovakia (or a *Tax ID* starting with `SK`), *Tax ID* = IČ DPH for the accounts and the deregistration list, *Company ID* = IČO for the reliability index |

The bank account you pay is compared with the register's list as an
**IBAN**. A Czech supplier's account may also be entered in the domestic form
(`19-2000145399/0800`); the Czech provider converts it to IBAN first.

## When the check runs {#checks}

- **Posting a vendor bill or a vendor credit note** — automatically, if the
  setting is on.
- **Posting an outbound supplier payment** — automatically, against the
  account the payment actually goes to. This is the moment the liability
  depends on, and weeks can pass between the bill and the payment.
- **Every day** — the scheduled action *Supplier reliability: re-check unpaid
  bills (CZ/SK)* re-checks posted bills that are not yet paid (or only partly
  paid) and were last checked more than 7 days ago, at most 200 per run, the
  oldest checks first.
- **By hand** — **Check supplier reliability**, under the recipient bank
  account on a vendor bill and under the vendor bank account on a supplier
  payment. It works in any state, including draft, and whether or not the
  setting is on.
- **On the contact** — *Actions → Check tax reliability* in the contact list
  or form asks for the rating only, for every selected contact's company.

Every check that gets a rating also writes it to the supplier's contact, as
**Tax Reliability** with the time of the check, next to its *Tax ID*.

A register that does not answer never stops a posting; the document then
shows *Not checked / unavailable*.

## What you see {#results}

On the vendor bill (and the payment), next to the bank account:

| Field | Meaning |
|---|---|
| Bank Account Check | *Paid account is registered*, *Paid account NOT registered*, *No bank account set* or *Not checked / unavailable* |
| Supplier Reliability | the register's rating, see the providers below |
| VAT Deregistration Listing | filled when the supplier is on the list of payers with grounds for cancelling the registration (Slovakia) |
| Registered Accounts (at check) | the accounts the register listed at that moment (bill only) |
| Reliability Checked On | when the snapshot was taken |

A warning banner appears at the top of the document, and the same text is
posted in the chatter, when:

- the account being paid is **not** among the registered accounts — with its
  own wording when the supplier has published no account at all;
- the rating is *Less reliable* or *Unreliable*;
- the supplier is on the deregistration list.

Each new check replaces the snapshot on the document; the chatter keeps the
earlier warnings. The snapshot fields are read-only and are not copied when
a bill is duplicated.

What to do about a warning is your decision: pay a published account
instead, or pay the VAT directly to the supplier's tax administrator
(§ 69c SK / § 109a CZ) and the rest to the supplier.

## Czech provider (ADIS) {#cz-provider}

[module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) asks
the Ministry of Finance web service *rozhraní CRP DPH* (the public part of
the VAT payer register) about suppliers whose country is the Czech Republic.
It needs no account or key. One request answers both questions:

| ADIS answer | Supplier Reliability |
|---|---|
| nespolehlivý plátce = ANO | Unreliable (warning) |
| nespolehlivý plátce = NE | Reliable |
| not found (not a VAT payer) | Unknown / not checked; the bank account is *Not checked / unavailable*, since a non-payer publishes no accounts and § 109 does not apply |

The published accounts come back in the domestic form
(předčíslí–číslo/kód banky); the module converts them, and an account typed
on the bill in that form, to IBAN before comparing. Accounts the register
publishes in another form (foreign IBANs) are compared as published. The Czech register has no deregistration list, so
that field stays empty for Czech suppliers.

## Slovak provider (Financial Administration open data) {#sk-provider}

[module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability)
uses the open-data service of the Finančná správa
(`opendata.financnasprava.sk`), which requires a free API key. Request a key
there and enter it under *Accounting → Configuration → Settings*, in the
**Supplier reliability check (CZ/SK)** setting, field **FS open-data API key**.
The key is shared by all companies of the database. Without it every Slovak
lookup is *Not checked / unavailable*.

| Question | Data set | Searched by |
|---|---|---|
| Registered bank accounts | `ds_dph_iban` (list of bank accounts of VAT payers) | IČ DPH (*Tax ID*) |
| Reliability | `ds_iz_ran` (index daňovej spoľahlivosti) | IČO (*Company ID*) |
| Deregistration list | `ds_dphz` (payers with grounds for cancelling the registration) | IČ DPH |

| Index daňovej spoľahlivosti | Supplier Reliability |
|---|---|
| vysoko spoľahlivý | Highly reliable |
| spoľahlivý | Reliable |
| menej spoľahlivý | Less reliable (warning) |
| not in the index | Unknown / not checked |

Before searching the deregistration list the module asks the service whether
that data set can be searched by IČ DPH. If it cannot, the field stays empty
and the check counts as unavailable rather than as a clean record.

## Limitations {#limitations}

- **Warns, never blocks.** Nothing stops you posting or paying an
  unregistered account.
- **A Slovak empty list warns.** When the Slovak list holds no account for
  the IČ DPH on the contact, the warning says the supplier has published
  none. For a platiteľ that is the liability case itself; but the Slovak data
  set cannot tell a platiteľ with no account from a subject that is not a
  platiteľ (for example a § 7 or § 7a registrant, whose IČ DPH is on no list
  of accounts). Check the supplier's registration before relying on it. A
  Czech supplier that ADIS does not hold as a plátce is reported as *Not
  checked / unavailable* instead.
- **Domestic account forms** are understood for Czech suppliers only. A Slovak
  account must be entered as IBAN.
- **Day of payment.** The law looks at the list on the day you give the
  payment order. The module checks when the payment is posted in Odoo; if you
  send the order to the bank later, check again.
- **Suppliers from other countries** are not checked. A supplier without a
  country (Czech provider) or without the identifier the register needs comes
  back *Not checked / unavailable*, without a warning.
- The **Tax Reliability** on the contact is the latest rating any check
  obtained; the bill and payment snapshots remain the record of what the
  register said at each moment.
- The Slovak deregistration data set name (`ds_dphz`) has not been confirmed
  against the live service; if it is wrong the field simply stays empty.
- A check records what the register said; it does not prove that the
  supplier will pay its VAT, nor that you could not have known otherwise.
