---
title: SK OSS VAT Return (DPOSS_EU, Union scheme)
summary: The Slovak One-Stop-Shop return for the Union scheme as the Finančná správa eForm DPOSS_EUv01, on the EU-wide return structure, validated against the official schema.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A Slovak taxable person that applies the **Union scheme** (*osobitná úprava
pre Úniu*) files a quarterly return of the VAT charged on distance sales of
goods and on services to consumers in other EU states. This module turns the
return computed by [module:l10n_cssk_oss_base](module:l10n_cssk_oss_base) into
the Finančná správa eForm **DPOSS_EUv01** (*Daňové priznanie k DPH — Úprava pre
Úniu*) and checks it against the official schema before it is attached.

Everything about preparing the return — the rows, corrections, exchange rates
and the export steps — is described in the
[shared guide](module:l10n_cssk_oss_base#usage). This page covers what is
Slovak.

## Legal background {#legal}

All references are to the [VAT Act, No. 222/2004 Z. z.](law:sk/2004/222);
statutory terms are given in Slovak.

- **What the scheme covers.** Distance sales of goods within the EU, services
  supplied to non-taxable persons by a taxable person not established in the
  member state of consumption, and certain domestic supplies through an
  electronic interface —
  [§ 68 ods. 1 písm. b)](law:sk/2004/222#paragraf-68.odsek-1.pismeno-b).
- **Registration.** A taxable person that decides to apply the scheme with
  Slovakia as the member state of identification notifies the tax office
  (*oznámenie o začatí činnosti*) and must then apply it to all such supplies —
  [§ 68b ods. 2](law:sk/2004/222#paragraf-68b.odsek-2) and
  [ods. 6](law:sk/2004/222#paragraf-68b.odsek-6).
- **Electronic filing.** Documents concerning the scheme are delivered to the
  tax office electronically —
  [§ 68 ods. 3](law:sk/2004/222#paragraf-68.odsek-3).
- **Period and deadline.** The tax period is the calendar quarter; a return is
  filed also for a quarter with no supplies, by the end of the following
  month, and a deadline falling on a weekend or holiday stays on that day —
  [§ 68b ods. 12](law:sk/2004/222#paragraf-68b.odsek-12).
- **Content.** The value of supplies without VAT, the VAT per rate, the rate
  and the total VAT due, per member state of consumption — and separately for
  goods dispatched from other member states and for services supplied from
  establishments elsewhere —
  [§ 68b ods. 13 to 16](law:sk/2004/222#paragraf-68b.odsek-13).
- **Euro.** Amounts are stated in euro, converted at the reference rate
  declared by the ECB or Národná banka Slovenska for the last day of the
  period, or the next day if none was declared for that day —
  [§ 68b ods. 17](law:sk/2004/222#paragraf-68b.odsek-17).
- **Payment.** The tax is paid in euro by the filing deadline, quoting the
  return — [§ 68b ods. 18](law:sk/2004/222#paragraf-68b.odsek-18).
- **Corrections.** A change to an earlier return goes into a later return,
  within three years of the original deadline, naming the member state, the
  period and the amount, at the rate that should have been used originally —
  [§ 68b ods. 19](law:sk/2004/222#paragraf-68b.odsek-19).

## The form {#form}

The module produces **DPOSS_EUv01**, the first and so far only vzor of the
Slovak Union-scheme return, in use since the scheme began on 1 July 2021. Slovak
forms are versioned per vzor and an old period uses the vzor in force then;
for this return there is only one, so there is **one form version**,
*DP DPH — úprava pre Úniu (DPOSS_EUv01)*, valid from 1 July 2021 with no end
date. Quarters before Q3 2021 were filed on the MOSS return, a different form.

The XML is not a Slovak structure but the EU-wide OSS return,
`OSSVATReturnMSCON`, against the schema `dposs_eu01.xsd` that Finančná správa
publishes for the eForm. The schema states version 1.0 of the EU structure,
which says nothing about a revision of the file, so the module pins it by size
and checksum, and a test fails if the bundled schema does not match.

What the file contains:

| Part | Content |
|---|---|
| `TraderID` | IČ DPH with the `SK` prefix |
| `Period` | year, quarter, and the start or end date when the registration began or ended during the quarter |
| `NilVatReturn` | `1` for a nil return, otherwise `0` |
| `MSIDSupplies` | supplies made from Slovakia: goods or services, member state of consumption (Greece as `EL`), rate with its type (standard or reduced), taxable amount and VAT |
| `MSESTSupplies` | supplies from an establishment or dispatch state elsewhere — the manual rows — with that state's VAT number or country code |
| `Corrections` | per corrected quarter and member state, the VAT correction |
| totals | VAT on supplies from Slovakia and from elsewhere, each for goods and services, and the grand total |
| `Balances` | per member state, this quarter's VAT plus corrections |
| `TotalVATAmountDue` | the sum of the **positive** balances only, as the eForm computes it; a member state left negative by corrections refunds that amount itself |

The elements carry the `vun:` namespace prefix. That is deliberate: the eForm's
own loader looks elements up by that name, and a file without the prefix
validates but loads into the portal form as an empty return.

## Setting it up {#setup}

- The company's **Tax ID** must be an IČ DPH: `SK` followed by 10 digits (a
  number entered without the prefix is accepted and written with it). The
  export refuses anything else.
- The form version is installed with the module. Choose
  *DP DPH — úprava pre Úniu (DPOSS_EUv01)* on each return.
- Set up Odoo's OSS taxes as the
  [shared guide](module:l10n_cssk_oss_base#setup) describes, including the
  Slovak 5 % rate.

## Filing {#usage}

1. Prepare and compute the return under *Účtovníctvo → Výkazy → Zákonné výkazy
   → Daňové priznania k DPH OSS* and confirm the ECB rates.
2. **Exportovať XML** (*Export XML*). The file is validated against
   `dposs_eu01.xsd` and attached.
3. Load the file into the eForm DPOSS_EUv01 on the Finančná správa portal,
   check it there and submit it from the portal.
4. **Označiť ako podané** (*Mark Submitted*) to keep the filed copy. The
   submission record opened by **Podať** (*File it*) holds the confirmation you
   download from the portal.

Pay the *Splatná DPH (EUR)* (*VAT due*) in euro by the filing deadline. The
module does not create the payment.

## Limitations {#limitations}

- Only the Union scheme. The non-Union and import returns are not built.
- There is no direct sending to Finančná správa from this module: the file is
  loaded into the portal's eForm by hand.
- A correction that has to be filed with the member state of consumption
  directly, after the three-year period, is not prepared here.
- A new vzor or a silent revision of the schema needs a module update.
- The checks are those described in the
  [shared guide](module:l10n_cssk_oss_base#limitations); the portal's own
  checks run only when the file is loaded there.
