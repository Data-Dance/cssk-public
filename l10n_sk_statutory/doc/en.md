---
title: SK Statutory Reference Data
summary: The Slovak tax offices and taxpayer types, so that a company can name the tax office its electronic filings go to.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Slovak electronic filings to the Financial Administration — the VAT return
(*daňové priznanie k DPH*) and the EC sales list (*súhrnný výkaz*) among them
— name the tax office (*daňový úrad*) they are addressed to. This module fills
the registers of [module:l10n_cssk_core](module:l10n_cssk_core) with Slovak
data:

- **the Slovak tax offices**: the eight regional offices *Daňový úrad
  Bratislava, Trnava, Trenčín, Nitra, Žilina, Banská Bystrica, Prešov* and
  *Košice*, and the *Daňový úrad pre vybrané daňové subjekty* (the office for
  selected taxpayers), each with its address and switchboard number;
- **the taxpayer types** *Fyzická osoba* (natural person) and *Právnická
  osoba* (legal entity).

Keeping this data in a Slovak module means none of it loads on a Czech
database.

## Setting it up {#setup}

*Settings → Users & Companies → Companies*, open the company and set:

| Field | What to enter |
|---|---|
| Tax Authority (*Daňový úrad*) | The tax office the company is registered with. |
| Entity Type (*Typ subjektu*) | *Právnická osoba* or *Fyzická osoba*. |

The tax office can also be set under *Accounting → Configuration → Settings*,
block *Czech / Slovak Localization*, field *Default tax authority*. The list of
offices is under *Accounting → Configuration → CZ/SK Localization → Tax
Authorities*.

## How the filings use it {#usage}

The Slovak filing schemas have no code list for tax offices: the office is a
free-text element (`danovyUrad`). The *Submission Code* (*Kód podania*) of
each office therefore holds its full name, for example *Daňový úrad Žilina*,
and that text is what [module:l10n_sk_vat_return](module:l10n_sk_vat_return)
and [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) write into the file.
Leave it unchanged unless the Financial Administration expects a different
wording.

## Limitations {#limitations}

- The list of offices is curated by hand; there is no official list in Odoo
  to load it from. If offices are merged or renamed, edit the records.
- Addresses and telephone numbers are not maintained automatically; check
  them if you use them.
- No Slovak filing reads the *Entity Type* at present; it is recorded for
  completeness.
- The records are loaded once and are not overwritten on upgrade, so your
  edits are kept, but corrections made in a later version do not reach an
  existing database either.
