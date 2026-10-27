---
title: SK Asset Protocols (zaradenie and vyradenie)
summary: The protocol on putting a fixed asset into use and the protocol on its disposal, printed from the asset register of either Odoo edition.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Around every fixed asset a Slovak accountant issues two internal documents:

- **Protokol o zaradení dlhodobého majetku do používania** — the asset is put
  into use: its inventory number (*inventárne číslo*), acquisition cost
  (*obstarávacia cena*), date, where it is kept and who is responsible for it;
- **Protokol o vyradení dlhodobého majetku** — the asset leaves the books:
  why, how, and the figures at that moment.

This module adds the data a protocol needs that an asset register does not
hold, and the two printouts. It works with whichever asset register is
installed:

| Edition | Asset register | Bridge (installs itself) |
|---|---|---|
| Community | OCA `account_asset_management` | [module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca) — see [Community](#community) |
| Enterprise | Odoo `account_asset` | [module:l10n_sk_asset_protocol_ee](module:l10n_sk_asset_protocol_ee) — see [Enterprise](#enterprise) |

Install this module; the matching bridge follows automatically. Without
either register the module installs but shows nothing.

## Legal background {#legal}

Neither protocol has a prescribed form. Both are internal accounting
documents (*účtovné doklady*), and an accounting document must contain the
particulars of [§ 10 ods. 1 of the Accounting Act](law:sk/2002/431#paragraf-10.odsek-1):
a verbal and numerical designation of the document, the content of the
transaction and its participants, the amount or the unit price and quantity,
the date it was drawn up, the date of the transaction where different, and
the signature of the person responsible for the transaction.

The printouts carry the document number and the date it was drawn up, the
company with its seat and IČO, the asset and its figures, the dates and
signature lines. What else the protocols contain is for your internal rules (*vnútorná smernica*);
treat these templates as a starting point.

## Recording the protocol data {#usage}

Open an asset and go to the tab **Protokoly (SK)**:

| Block | Field | Meaning |
|---|---|---|
| Zaradenie | *Inventory number* (inventárne číslo) | The number in your asset register. If left empty, the protocols print the register's own reference instead (see the bridges). |
| | *Location* (miesto umiestnenia) | Where the asset is kept. |
| | *Responsible person* (zodpovedná osoba) | A contact. |
| | *Commissioning note* (poznámka k zaradeniu) | Technical condition, accessories, documents forming an annex. |
| | *Commissioning protocol date* (dátum vyhotovenia protokolu o zaradení) | The date the protocol was drawn up. Empty: the protocol shows the day it is printed; fill it in so that a reprint stays the same. |
| Vyradenie | *Disposal method* (spôsob vyradenia) | Sale (predaj), liquidation (likvidácia), donation (darovanie), shortage or damage (manko alebo škoda), contribution to another company (vklad do inej spoločnosti), other. |
| | *Disposal reason* (dôvod vyradenia) | Free text. |
| | *Disposal protocol date* (dátum vyhotovenia protokolu o vyradení) | As for the commissioning protocol. |

The disposal method is recorded for the protocol only. It does not dispose
of the asset or post anything; do that with the register's own disposal
function.

## Printing {#printing}

From the asset, *Print*:

Both protocols open with the document number — **ZP-** (zaradenie) or
**VP-** (vyradenie) followed by the inventory number — the date it was drawn
up, and the company's name, seat and IČO.

- **Protokol o zaradení majetku** — date put into use, asset
  name, inventory number, *obstarávacia cena*, *odpisový plán* (the asset
  profile or model), *miesto umiestnenia*, *zodpovedná osoba*, the
  commissioning note, and signature lines *Majetok odovzdal* / *Majetok
  prevzal*.
- **Protokol o vyradení majetku** — disposal date, asset name,
  inventory number, date put into use, *obstarávacia cena*, *oprávky
  (odpísané)*, *zostatková cena*, *spôsob* and *dôvod vyradenia*, a note that
  the documents evidencing the disposal are an integral part of the protocol,
  and signature lines *Vyradenie navrhol* / *Vyradenie schválil*.

The figures always add up: *obstarávacia cena* − *oprávky* = *zostatková
cena*, the net book value including any salvage value. *Oprávky* are the
posted depreciation only; on the disposal protocol of a disposed asset they
do not include the residual value written off, which is the *zostatková
cena*.

The printouts are in Slovak whatever the user's language; dates follow the
user's date format. Both can be printed
at any time; the disposal protocol of an asset that has not been disposed of
simply has no disposal date.

## Community: OCA asset register {#community}

[module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca)
installs itself when this module and OCA `account_asset_management` are both
installed. Assets are under *Accounting → Assets → Assets* (the OCA menu,
which may show in English). The protocols take:

| On the protocol | From the OCA asset |
|---|---|
| Dátum zaradenia | *Asset Start Date* |
| Obstarávacia cena | *Purchase Value* |
| Oprávky (odpísané) | the posted depreciation lines (not the removal line) |
| Zostatková cena | *Purchase Value* − oprávky (salvage value included) |
| Odpisový plán | *Asset Profile* |
| Dátum vyradenia | *Asset Removal Date*, set by the register's removal wizard |
| Inventárne číslo, if empty | *Reference* |

## Enterprise: Odoo asset register {#enterprise}

[module:l10n_sk_asset_protocol_ee](module:l10n_sk_asset_protocol_ee) installs
itself when this module and Enterprise `account_asset` are both installed.
Assets are under *Accounting → Accounting → Assets & Liabilities → Assets*.
The protocols take:

| On the protocol | From the Enterprise asset |
|---|---|
| Dátum zaradenia | *Acquisition Date* |
| Obstarávacia cena | *Original Value* of the asset and of its value increases (child assets) |
| Oprávky (odpísané) | posted depreciation entries of the asset and its value increases, plus depreciation imported as already done; not the disposal or sale entry |
| Zostatková cena | obstarávacia cena − oprávky (salvage value included) |
| Odpisový plán | *Asset Model* |
| Dátum vyradenia | *Disposal Date*, set when the asset is disposed of or sold |
| Inventárne číslo, if empty | the asset's name |

The two bridges cannot be installed together, because the two registers
exclude each other.

## Limitations {#limitations}

- The document number is derived from the inventory number (or the
  register's own reference); Odoo does not check that inventory numbers are
  unique.
- The protocols do not record the tax depreciation group or tax residual
  value; those come from [module:account_asset_tax](module:account_asset_tax).
- *Responsible person* is any contact; nothing ties it to an employee or to
  the *hmotne zodpovedná osoba* of an inventory count.
