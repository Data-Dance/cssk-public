---
title: CZ Asset Protocols (zařazení and vyřazení)
summary: The protocol on putting a fixed asset into use and the protocol on its disposal, printed from the asset register of either Odoo edition.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Around every fixed asset a Czech accountant issues two internal documents:

- **Protokol o zařazení dlouhodobého majetku do užívání** — the asset is put
  into use: its inventory number (*inventární číslo*), valuation (*ocenění*,
  usually the *pořizovací cena*), date, where it is kept and who is
  responsible for it;
- **Protokol o vyřazení dlouhodobého majetku** — the asset leaves the books:
  why, how, and the figures at that moment.

This module adds the data a protocol needs that an asset register does not
hold, and the two printouts. It works with whichever asset register is
installed:

| Edition | Asset register | Bridge (installs itself) |
|---|---|---|
| Community | OCA `account_asset_management` | [module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca) — see [Community](#community) |
| Enterprise | Odoo `account_asset` | [module:l10n_cz_asset_protocol_ee](module:l10n_cz_asset_protocol_ee) — see [Enterprise](#enterprise) |

Install this module; the matching bridge follows automatically. Without
either register the module installs but shows nothing.

## Legal background {#legal}

Neither protocol has a prescribed form. Both are internal accounting
documents (*účetní doklady*), and an accounting document must contain the
particulars of [§ 11 odst. 1 of the Accounting Act](law:cz/1991/563):

- a) the designation of the document,
- b) the content of the transaction and its participants,
- c) the amount, or the unit price and the quantity,
- d) the moment the document was made out,
- e) the moment of the transaction, where different from d),
- f) the signature record of the person responsible for the transaction and
  the signature record of the person responsible for posting it.

The printouts carry the designation and the date the document was made out,
the company with its seat and IČO, the asset and its figures, the date of
putting into use or of disposal, and signature lines — including the two
that letter f) asks for. What else the protocols contain is for your internal
rules (*vnitřní předpis*); treat these templates as a starting point.

Three further sources shaped the content:

- An asset becomes a fixed asset when it is brought into a condition fit for
  use ([§ 7 odst. 11 of Decree No. 500/2002 Sb.](law:cz/2002/500)); that is
  the date the commissioning protocol records. Depreciation follows a
  depreciation plan ([§ 28 odst. 6 of the Accounting Act](law:cz/1991/563),
  [§ 56 odst. 4 of the decree](law:cz/2002/500)), which is why the protocol
  names the plan.
- Český účetní standard pro podnikatele č. 013 (Dlouhodobý nehmotný a hmotný
  majetek) lists the ways an asset is disposed of (bod 5.4) — the choices of
  *Disposal method* below — and defines the *zůstatková cena* as the
  valuation less *oprávky* (bod 4.4).
- For tax purposes an asset is classified into a depreciation group
  (*odpisová skupina*) in its first year of depreciation and is depreciated
  straight-line or accelerated
  ([§ 30 odst. 1 and 2 of the Income Taxes Act](law:cz/1992/586)). Czech
  practice states both on the commissioning protocol; see
  [Printing](#printing).

## Recording the protocol data {#usage}

Open an asset and go to the tab **Protokoly (CZ)**:

| Block | Field | Meaning |
|---|---|---|
| Zařazení | *Inventory number* (inventární číslo) | The number in your asset register. If left empty, the protocols print the register's own reference instead (see the bridges). |
| | *Location* (místo umístění) | Where the asset is kept. |
| | *Responsible person* (odpovědná osoba) | A contact. |
| | *Commissioning note* (poznámka k zařazení) | Technical condition, accessories, documents forming an annex. |
| | *Commissioning protocol date* (datum vyhotovení protokolu o zařazení) | The date the protocol was made out. Empty: the protocol shows the day it is printed; fill it in so that a reprint stays the same. |
| Vyřazení | *Disposal method* (způsob vyřazení) | Sale (prodej), liquidation (likvidace), donation or other gratuitous transfer (dar nebo jiný bezúplatný převod), contribution to another business corporation (vklad do jiné obchodní korporace), transfer under legal regulations (převod na základě právních předpisů), damage or shortage (škoda nebo manko), transfer from business to personal use (převod z podnikání do osobního užívání), other. |
| | *Disposal reason* (důvod vyřazení) | Free text. |
| | *Disposal protocol date* (datum vyhotovení protokolu o vyřazení) | As for the commissioning protocol. |

The disposal method is recorded for the protocol only. It does not dispose
of the asset or post anything; do that with the register's own disposal
function.

## Printing {#printing}

From the asset, *Print*:

Both protocols open with the designation of the document — **ZP-**
(zařazení) or **VP-** (vyřazení) followed by the inventory number — the date
it was made out, and the company's name, seat and IČO.

- **Protokol o zařazení majetku** — date put into use, asset name, inventory
  number, *ocenění (pořizovací cena)*, *účetní odpisový plán* (the asset
  profile or model), *místo umístění*, *odpovědná osoba*, the commissioning
  note, and signature lines *Majetek předal* / *Majetek převzal*.
- **Protokol o vyřazení majetku** — disposal date, asset name, inventory
  number, date put into use, *ocenění (pořizovací cena)*, *oprávky*,
  *zůstatková cena*, *způsob* and *důvod vyřazení*, a note that the
  documents evidencing the disposal are an integral part of the protocol,
  and signature lines *Vyřazení navrhl* / *Vyřazení schválil*.

Both end with the two signature lines of § 11 odst. 1 písm. f): *Osoba
odpovědná za účetní případ* and *Osoba odpovědná za zaúčtování*.

Where [module:account_asset_tax](module:account_asset_tax) is installed and
the asset has tax depreciation switched on with a Czech depreciation group,
the commissioning protocol adds two rows: *Odpisová skupina (daňové odpisy)*
and *Způsob daňového odpisování* (rovnoměrné, zrychlené or mimořádné).
Without that module the rows are left out.

The figures always add up: *ocenění* − *oprávky* = *zůstatková cena*, the net
book value including any residual value the plan leaves undepreciated.
*Oprávky* are the posted depreciation only; on the disposal protocol of a
disposed asset they do not include the residual value written off, which is
the *zůstatková cena*.

The printouts are in Czech whatever the user's language, the disposal method
included; dates follow the user's date format. Both can be printed at any
time; the disposal protocol of an asset that has not been disposed of simply
has no disposal date.

## Community: OCA asset register {#community}

[module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca)
installs itself when this module and OCA `account_asset_management` are both
installed. Assets are under *Accounting → Assets → Assets* (the OCA menu).
The protocols take:

| On the protocol | From the OCA asset |
|---|---|
| Datum uvedení do užívání | *Asset Start Date* |
| Ocenění (pořizovací cena) | *Purchase Value* |
| Oprávky | the posted depreciation lines (not the removal line) |
| Zůstatková cena | *Purchase Value* − oprávky (salvage value included) |
| Účetní odpisový plán | *Asset Profile* |
| Datum vyřazení | *Asset Removal Date*, set by the register's removal wizard |
| Inventární číslo, if empty | *Reference* |

## Enterprise: Odoo asset register {#enterprise}

[module:l10n_cz_asset_protocol_ee](module:l10n_cz_asset_protocol_ee) installs
itself when this module and Enterprise `account_asset` are both installed.
Assets are under *Accounting → Accounting → Assets & Liabilities → Assets*.
The protocols take:

| On the protocol | From the Enterprise asset |
|---|---|
| Datum uvedení do užívání | *Acquisition Date* |
| Ocenění (pořizovací cena) | *Original Value* of the asset and of its value increases (child assets) |
| Oprávky | posted depreciation entries of the asset and its value increases, plus depreciation imported as already done; not the disposal or sale entry |
| Zůstatková cena | ocenění − oprávky (salvage value included) |
| Účetní odpisový plán | *Asset Model* |
| Datum vyřazení | *Disposal Date*, set when the asset is disposed of or sold |
| Inventární číslo, if empty | the asset's name |

The two bridges cannot be installed together, because the two registers
exclude each other.

## Limitations {#limitations}

- The designation of the document is derived from the inventory number (or
  the register's own reference); Odoo does not check that inventory numbers
  are unique.
- The row is labelled *Ocenění (pořizovací cena)* whatever the valuation
  basis; for an asset valued at *reprodukční pořizovací cena* or *vlastní
  náklady* adapt the template.
- The date put into use is the register's start or acquisition date; the
  protocols do not keep a separate date of acquisition.
- The protocols do not print the tax entry price (*vstupní cena*) or the tax
  residual value; those are kept by
  [module:account_asset_tax](module:account_asset_tax).
- *Responsible person* is any contact; nothing ties it to an employee or to
  the *hmotně odpovědná osoba* of an inventory count.
- The signature lines are for handwritten signatures; the module does not
  create electronic signature records.
