---
title: Slovak Base Localization (DIČ)
summary: Gives the Slovak DIČ — the income-tax identifier — its own field on contacts and companies, separate from the VAT number and the company registry number.
verified: 19.0.2.0.0
---

## What it is for {#purpose}

A Slovak business has up to three identifiers, and they are different
numbers:

| Identifier | Meaning | Field in Odoo |
|---|---|---|
| **IČO** | *identifikačné číslo organizácie*, company registry number | *Company ID* (`company_registry`) |
| **DIČ** | *daňové identifikačné číslo*, tax identification number assigned on registration for income tax, ten digits | **DIČ**, added by this module |
| **IČ DPH** | *identifikačné číslo pre daň*, VAT number, usually `SK` followed by the DIČ | *Tax ID* / VAT (`vat`) |

Someone registered for income tax but not for VAT has a DIČ and **no IČ DPH**.
Odoo's VAT field cannot hold that, and Odoo's Slovak localization has a DIČ
field on the company only (*Income Tax ID*), not on customers and vendors. This
module adds the DIČ to every contact and makes the company's DIČ the same
value.

Other modules read it from here: the Slovak invoice layout prints it next to
the IČ DPH, and the income-tax returns, financial statements and payroll
declarations put it into their XML. With
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) it
is filled from the state registers.

The Czech Republic needs no such field: there *DIČ* is the VAT number, which
Odoo's VAT field already holds.

## Legal background {#legal}

The tax administrator assigns the DIČ when a taxable person registers, and the
person must quote it in all dealings with the administrator —
[§ 67 ods. 7 of the Tax Procedure Code No. 563/2009 Z. z.](law:sk/2009/563#paragraf-67.odsek-7).

## Where to enter it {#usage}

- **Contacts.** On a contact whose country is Slovakia, the **DIČ** field
  appears just before the VAT number. It belongs to the company, not to its
  individual contact persons: a person under a company shows and uses the
  company's DIČ, the same way Odoo treats the VAT number.
- **Your company.** *Settings → Companies → your company*: the **DIČ** field
  appears after the VAT number when the company's country is Slovakia. It is
  the DIČ of the company's own contact, so entering it in either place changes
  both.

Odoo's own *Income Tax ID* field from the Slovak localization is now the same
value and is hidden from the company form, so the number is not shown twice.

The field is not validated; type the ten digits as issued.

## Upgrading {#upgrade}

On installation the module collects a DIČ already entered elsewhere — in the
company's *Income Tax ID*, in the older shared field of the CZ/SK core, or in
the company field that some Slovak payroll modules kept on their own — and
moves it to the new field. A value already in the new field is never
overwritten. Nothing needs to be done by hand.

## Limitations {#limitations}

- No format check: the DIČ is not checked for length, digits or agreement
  with the IČ DPH.
- The field is shown only for contacts and companies whose country is
  Slovakia.
- Odoo's own Slovak translation labels the VAT number field *DIČ* on some
  screens. Do not confuse it with this field: the VAT field holds the IČ DPH
  with the `SK` prefix.
- If a single import or API call sets both the company *DIČ* and *Income Tax
  ID* to different values, it is refused, because they are one number.
