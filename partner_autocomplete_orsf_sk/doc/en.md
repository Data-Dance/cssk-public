---
title: Partner Autocomplete from the Slovak Registers (ORSF)
summary: Fills Slovak contacts from the state registers through ORSF — identity, address, IČ DPH, DIČ, register entry, status and activities — and refreshes many contacts at once.
verified: 19.0.1.4.1
---

## What it is for {#purpose}

ORSF (orsf.sk) publishes the Slovak state registers through one open
interface: the register of legal entities (RPO), the commercial register
(ORSR), the trade register (ŽRSR), the register of financial statements (RÚZ)
and the Financial Administration's list of VAT payers. This module makes ORSF
a provider of partner autocomplete, so that a Slovak contact is filled from the
register instead of being typed, and keeps it current later.

It plugs into the
[partner-autocomplete dispatcher](module:partner_autocomplete_dispatcher), which
decides which register is asked: a contact whose country is Slovakia is looked
up in ORSF from every company, whichever provider the company has chosen.

Everything this module does works without an ORSF account. ORSF data is
licensed CC-BY 4.0; if you republish it, credit ORSF and the source registers.

## Setting it up {#setup}

*Settings → General Settings*, block **Contacts**, **Provider**: choose
**ORSF.SK**. Its settings appear below:

| Setting | What it does |
|---|---|
| ORSF API base URL | Leave empty for ORSF's public address. Only an `http(s)` address is accepted. |
| ORSF API token | Optional token from an ORSF account. It raises the request quota and unlocks the full address of a sole trader, which ORSF otherwise withholds. Not needed for anything else. |
| ORSF account e-mail / ORSF account password | Needed only by [module:partner_autocomplete_orsf_sk_related_parties](module:partner_autocomplete_orsf_sk_related_parties). The password is stored **in plain text** in the database and in every backup: use a dedicated ORSF account, never a personal one. |
| Request timeout (s) | How long to wait for ORSF. Default 15. |
| ORSF: fill Company ID | Write the IČO into *Company ID* as well as into any mapped field. On by default. |
| ORSF: set company type | Make the contact an *Individual* for a sole trader (živnostník) and a *Company* otherwise, following the register. On by default. |
| ORSF: format PSČ as 851 01 | ORSF returns the postal code as five digits; Slovak documents write it 3 + 2. On by default. |

The three *ORSF:* options are kept per company; the rest apply to the whole
database.

### Where register values are written {#mapping}

Under **Field mapping** each register value has a target field on the contact.
Clear one and that value is not stored; aim it at a field of your own and the
value follows.

| Mapping | Standard field | Provided by |
|---|---|---|
| IČO | *Company ID* | Odoo |
| DIČ | DIČ | [module:l10n_sk_base](module:l10n_sk_base) |
| SK NACE | NACE (main activity) | [module:partner_nace](module:partner_nace) |
| Právna forma, Register, Registrový súd, Číslo zápisu, Stav subjektu, Veľkostná kategória, Dátum vzniku, Dátum zániku | the register fields of the same names | [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) |
| Druh registrácie DPH (§), Platiteľ DPH od | Druh registrácie DPH, Platiteľ DPH od | [module:l10n_sk_vat_registration](module:l10n_sk_vat_registration) |

The mappings point at the standard fields automatically when this module is
installed. If you install one of the modules in the right-hand column later,
press **Use the standard SK fields** to point the mappings at its fields. A
blue box above the mapping names the modules that are still missing. Only with
those modules do the values mean something elsewhere in Odoo — the § 3a
statement, the § 69 ods. 12 warning, the banner on a dissolved partner.

## Filling in a contact {#usage}

Type into the name field of a new contact:

- **a company name** (at least three characters) — up to five matches from the
  register's full-text index;
- **an IČO** (6 to 8 digits) — the register is asked for that number directly.

A subject that is not active carries the register's own status word in the
suggestion, e.g. *Firma s.r.o. (12345678) — zrušená*. It may still be the right
choice for an old document; it is labelled so that a defunct IČO does not land
on a new invoice unnoticed.

Typing a Slovak IČ DPH into the VAT number field (*Tax ID*) finds its holder.
Only an exact match is offered: the register is asked to confirm that the
subject holds that IČ DPH right now.

Picking a suggestion fills:

| Value | Note |
|---|---|
| Name, street, city, PSČ, country | |
| VAT number (*Tax ID*) | the IČ DPH, **only while the register shows a live VAT registration**. A withdrawn IČ DPH is not written. |
| *Company ID* | the IČO, if *ORSF: fill Company ID* is on |
| Company / Individual | if *ORSF: set company type* is on |
| Mapped values | see [the mapping](#mapping) |
| Register lists | with [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry): predmety podnikania, filed účtovné závierky, previous names and seats, and the time the register was checked. Each list is replaced, not appended to. |

## Keeping contacts current {#refresh}

Three actions in the contact list, *Actions* menu:

| Action | Reads | Good for |
|---|---|---|
| **Update** (from the dispatcher) | the full register record, one contact at a time | a few contacts whose register entry, VAT paragraph or activities matter |
| **Refresh identity from ORSF (bulk)** | identity only, up to 100 IČOs per request | the whole partner base |
| **Fill missing DIČ from ORSF** | the DIČ only, up to 100 IČOs per request | contacts that need a DIČ (for example for the Peppol identifier *0245:DIČ*) without having anything else rewritten |

ORSF allows far fewer full-record reads per minute than identity lookups, so
**Update** on a long selection stops returning data partway through.

### Bulk refresh {#bulk}

**Refresh identity from ORSF (bulk)** takes the IČO an earlier autocomplete
recorded on each selected contact, or its *Company ID*, asks the register for
all of them in batches and rewrites each contact's name, address, IČ DPH and
the mapped identity values: DIČ, právna forma, register, status, SK NACE, dátum
vzniku and zániku. It does not touch register office and číslo zápisu, the VAT
paragraph, activities or filings — run **Update** for those.

A notification reports how many contacts were updated, how many IČOs the
register does not hold and how many contacts had no usable IČO.

A contact person inside a company is **skipped** and counted among those
without a usable IČO. It carries the company's IČO in *Company ID*, copied
there by Odoo, and looking that up would overwrite the person's name and
address with the company's. *Company ID* is used only on a company or on a
person with no parent company (a sole trader) — the same rule as **Update**.

### Filling a missing DIČ {#dic}

**Fill missing DIČ from ORSF** writes the DIČ into contacts whose **DIČ** is
empty and changes nothing else — no name, address or IČ DPH. A DIČ already on
a contact, typed by hand or not, is never overwritten, so the action can be
run again at any time. It needs
[module:l10n_sk_base](module:l10n_sk_base), which adds the field; without it
the action only says so. A notification counts the contacts filled, the IČOs
not in the register, those with no DIČ published and those without a usable
IČO.

## Limitations {#limitations}

- A withdrawn IČ DPH is not written, but one already on the contact is **not
  removed** either, by **Update** or by the bulk refresh. Check the VAT status
  of a deregistered partner yourself, or use [module:l10n_cssk_vies](module:l10n_cssk_vies).
- ORSF's copy of the registers can be incomplete — for example a company with
  no register court or číslo zápisu although it is in ORSR. With
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) the contact's
  register tab has a button that asks ORSF to re-read the company; run
  **Update** a minute later.
- Without an API token, ORSF returns only the city of a sole trader, not the
  street and PSČ.
- No answer from ORSF — an outage, a timeout, a rate limit — shows as no
  suggestions or *no data returned*, never as an error message. The server log
  has the cause.
- Only Slovak subjects. Other countries go to their own provider or to the
  company's provider.
