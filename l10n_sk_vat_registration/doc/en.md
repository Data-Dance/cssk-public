---
title: SK VAT Registration Category (§ 4 / § 7 / § 7a)
summary: Records under which paragraph of the Slovak VAT Act a partner's IČ DPH was issued, and warns when a domestic reverse charge is aimed at a § 7 or § 7a registrant, who is not a platiteľ.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

An IČ DPH does not mean the same thing for everyone who holds one. A Slovak
business registered under **§ 7** (acquisition of goods from another member
state) or **§ 7a** (services received from or supplied to another member
state) gets a valid IČ DPH, which VIES confirms — but it is **not a platiteľ
dane** (VAT payer). It does not charge VAT on domestic supplies, does not
deduct input VAT, and the domestic reverse charge (*prenesenie daňovej
povinnosti*) under § 69 ods. 12 cannot be applied to it.

VIES answers only valid / not valid. This module adds the registration
paragraph to the contact and warns when an invoice applies the domestic
reverse charge to a customer who is not a platiteľ.

## Legal background {#legal}

All references are to the [zákon o DPH](law:sk/2004/222).

- [§ 4](law:sk/2004/222#paragraf-4) — a taxable person established in
  Slovakia becomes a **platiteľ**, for example after its turnover exceeds
  EUR 50,000 in a calendar year;
  [§ 4b](law:sk/2004/222#paragraf-4b) — group registration;
  [§ 4c](law:sk/2004/222#paragraf-4c) — group registration ex officio;
  [§ 5](law:sk/2004/222#paragraf-5) — a foreign person becomes a platiteľ by
  supplying in Slovakia.
- [§ 7](law:sk/2004/222#paragraf-7) — a person not obliged to register under
  § 4 or § 5 (or a non-taxable legal person) registers before its
  acquisitions of goods from other member states reach EUR 14,000 in a
  calendar year, or voluntarily.
- [§ 7a](law:sk/2004/222#paragraf-7a) — a taxable person not obliged to
  register under § 4 registers before receiving a service from a foreign
  person for which it must pay the tax, or before supplying a service whose
  place of supply is in another member state.
- [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12) — the domestic reverse
  charge applies when **both** the supplier and the customer are platitelia
  with an IČ DPH assigned under § 4, § 4b, § 4c or § 5. A § 7 / § 7a
  registrant is neither, so the supplier charges and pays Slovak VAT as usual.

## Setting it up {#setup}

Nothing to configure. On the contact form, below the IČ DPH (*Tax ID*), two
fields appear for Slovak partners and partners without a country:

| Field | Meaning |
|---|---|
| Druh registrácie DPH | the paragraph the IČ DPH was issued under: § 4, § 4b, § 4c, § 5, § 7 or § 7a; § 6 *zásielkový predaj* for a distance-selling registration made before 1 July 2021 |
| Platiteľ DPH od | the day the VAT registration took effect, per the Finančná správa record (shown once the category is set) |

Fill them in by hand, or let
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)
fill them from the register when you look a company up. Values the register
writes in near-miss forms (`§4`, `§ 7a`, `7A`) are recognised; anything
unrecognised leaves the field **empty**, never "not a platiteľ".

## The warning on invoices {#warning}

On a customer invoice of a Slovak company a yellow warning appears at the
top, in Slovak with an English translation, when all of these hold:

- the customer's category is **§ 7** or **§ 7a**;
- the customer's country is Slovakia, or not set;
- a line carries a tax marked as a Slovak domestic reverse charge (the
  *SK Reverse Charge (§69/12)* flag of
  [module:l10n_sk_invoice](module:l10n_sk_invoice)).

When the invoice is posted the same text is written to its chatter. The
warning **never blocks** posting: correct the taxes yourself — the supply is
taxed with ordinary Slovak VAT.

Without [module:l10n_sk_invoice](module:l10n_sk_invoice) there is no reverse
charge flag on taxes, and the check stays silent.

## Limitations {#limitations}

- **The category is only as current as its last update.** Nothing refreshes
  it on a schedule; a customer who becomes a § 4 platiteľ keeps its old
  category until you or the register lookup change it.
- **Only the domestic reverse charge is checked.** Other consequences of a
  § 7 / § 7a registration (for example on intra-Community supplies or on the
  kontrolný výkaz) are not.
- **The § 6 option is historical.** It stands for the distance-selling
  registration of § 6 as worded until 30 June 2021, whose holders were
  platitelia, and counts as one. The § 6 in force today is the platiteľ's
  duty to notify its bank accounts and registers nobody, so a current
  register record should never carry it.
- **Platiteľ DPH od** is the registration date for every category, including
  § 7 / § 7a registrants, who are not platitelia.
- Vendor bills are not checked.
