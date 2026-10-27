---
title: Partner Autocomplete from State Registers (CZ/SK)
summary: Fills contacts from the Czech and Slovak business registers instead of Odoo's paid autocomplete service, choosing the register by the partner's country.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

Odoo's own partner autocomplete looks companies up in Odoo's paid
in-app-purchase service. For Czech and Slovak partners the authoritative
source is the state business register, keyed by the company's
identification number (IČO). This module is the switch between the two: it
lets each company choose a **provider** for partner autocomplete and sends
name searches, VAT-number searches and the final "fill in the contact" step to
that provider.

On its own it does nothing visible. It is installed together with one or both
providers:

| Provider | Register | Countries | Guide |
|---|---|---|---|
| ARES.CZ | ARES, the Czech register of economic subjects | CZ | [below](#ares) |
| ORSF.SK | ORSF, an open aggregation of the Slovak registers (RPO, ORSR, ŽRSR, RÚZ, Finančná správa) | SK | [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk) |

## Setting it up {#setup}

1. Install a provider module. The dispatcher comes with it.
2. *Settings → General Settings*, block **Contacts**: **Partner Autocomplete**
   must be enabled.
3. Under it, **Provider** — choose the register for the current company. Odoo's
   "buy credits" link is replaced by this choice. Provider-specific settings
   appear below it when that provider is selected.

The provider is stored per company. Switch to each company and set it there.

Two choices are not registers:

- **Odoo IAP** hands the search back to Odoo's own service, exactly as without
  this module. Every search for a partner whose country no installed provider
  reads leaves for Odoo.
- **None** looks nothing up outside the national registers. A partner in a
  provider's country is still looked up there (see below); anything else finds
  nothing, and nothing is sent to Odoo.

Until version 19.0.1.2.0 **None** was the label of what is now **Odoo IAP**: a
company that had chosen it keeps using Odoo's service. Choose **None** again if
that is not what you want.

## Which register is asked {#routing}

The country decides first, the company's choice second:

- A provider declares the countries whose register it reads — ARES reads CZ,
  ORSF reads SK. When the contact's **Country** is one of them (or, in a VAT
  search, the VAT number starts with that country's prefix), that provider is
  asked, **whatever the company has chosen**. A Slovak company can autocomplete
  a Czech supplier from ARES and the other way round, as long as both providers
  are installed.
- For any other country, or with no country, the company's **Provider** is
  asked.
- When you pick a suggestion, the details are fetched from the same register
  that offered it. This matters because a Czech and a Slovak IČO both have
  eight digits.

## Filling in a contact {#usage}

Type at least three characters of the company name — or its IČO — into the
name field of a new contact, or a VAT number into **Tax ID**, and pick one of
the suggestions. The provider fills the address, the identifiers and whatever
else it supports; see the provider's guide for the exact list.

What the providers return can include **bank accounts** and **contacts**. On the
company form (*Settings → Companies*) the module therefore adds two tabs,
*Bank Accounts* and *Contacts*, so that autocompleting your own company can
fill them too. When the provider replaces a list (bank accounts, register
lists), the old rows are removed rather than duplicated.

## Updating existing contacts {#update}

Select one or more contacts in the list and run *Actions → Update*. Each
contact is looked up again in its register and overwritten with what the
register says.

The register asked is the one an earlier autocomplete recorded on the contact,
otherwise the register of the contact's **Country**, otherwise the company's
**Provider** — the same order as for a search.

The number used for the lookup is the contact's own:

- the IČO a previous autocomplete recorded on it, or
- **Company ID** (*company_registry*) — but only on a company, or on a
  person with no parent company (a sole trader). A contact person inside a
  company carries the company's number, copied there by Odoo, and is
  **skipped**: looking up that number would overwrite the person with the
  company's name and address.

When more than one contact was selected, or something went wrong, a
notification counts the outcomes: *updated*, *skipped* (nothing to search by),
*with no data returned*, and *failed* (the cause is in the server log).

The registers limit how many full records may be read per minute, so
**Update** on a large selection starts returning nothing partway through. That
shows up as *with no data returned*, not as an error. For many Slovak contacts
use ORSF's [bulk refresh](module:partner_autocomplete_orsf_sk#bulk) instead.

## Enriching contacts during an import {#import}

An import file may carry a column **Import Enrich Company** holding the IČO.
Each imported contact with a value in it is looked up and filled in from the
register as it is created. Contacts created by hand are never looked up
behind your back: saving a new company with a **Company ID** does not trigger
a lookup.

## ARES (Czech Republic) {#ares}

[module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz)
reads the public ARES service of the Czech Ministry of Finance. No account or
key is needed.

- **Searching.** By company name: the first five matches, shown as *name, city
  (IČO)*. Typing an IČO as digits offers that company. A Czech VAT number
  typed into **Tax ID** finds the company when it is a legal person's DIČ
  (*CZ* + the eight-digit IČO) and ARES confirms that DIČ for it.
- **Filled in:** name, street, PSČ, city, country and **Tax ID** with the DIČ
  as ARES publishes it.
- **Settings** (shown when ARES is the company's provider):

  | Setting | What it does |
  |---|---|
  | IČO | The contact field that receives the IČO. Empty by default, so the IČO is not stored anywhere until you choose a field, typically *Company ID*. |
  | Prevailing activity (CZ-NACE 2025) | The contact field that receives the prevailing activity from ARES's copy of the statistical register (RES). Points at *NACE (main activity)* automatically when [module:partner_nace](module:partner_nace) is installed. Costs one extra request per lookup; leave it empty to skip it. |

- **Limits.** ARES offers no search by VAT number; a natural person's DIČ
  (ten digits, derived from the birth number) has no IČO to try and finds
  nothing. ARES returns the DIČ whether or not the company
  is currently registered for VAT; check the VAT status before relying on it
  for reverse charge. Bank accounts and contact persons are not filled.

## Limitations {#limitations}

- A provider answering with nothing looks the same whether the company does not
  exist, the register is down or the rate limit was hit. The server log tells
  them apart.
- The settings field labels of this module are not translated.
