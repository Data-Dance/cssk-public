---
title: SK Inventory Verification (inventarizácia)
summary: The Slovak statutory inventory verification as records — the inventarizácia with its three dates, the inventúrne súpisy with quantities and prices, and the inventarizačný zápis comparing them with the books.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

Before the financial statements are drawn up, a Slovak accounting entity must
verify that what its books say it owns and owes matches reality. This is the
**inventarizácia** (inventory verification). It produces two kinds of records:
**inventúrne súpisy** (count sheets: what was actually found) and one
**inventarizačný zápis** (the closing record: how the count compares with the
books).

The module keeps those records in Odoo: one inventarizácia document per
exercise, any number of súpisy under it, and the zápis fields on the
inventarizácia itself. For an account verified from documents, the book
balance is read from the general ledger. Both records print as PDF.

It also books the inventory differences — manká, schodky and prebytky — as a
draft journal entry dated in the period verified, linked to the
inventarizácia. Impairment and other valuation adjustments are not inventory
differences ([§ 30 ods. 6](law:sk/2002/431#paragraf-30.odsek-6)) and stay with
the accountant.

The screens, fields and printouts are in Slovak, because the field names are
the statute's own terms. This page quotes them as they appear.

## Legal background {#legal}

All references are to the [Accounting Act](law:sk/2002/431).

- **When.** Under [§ 29 ods. 2](law:sk/2002/431#paragraf-29.odsek-2) the
  inventarizácia is carried out as at the day the ordinary or extraordinary
  financial statements are drawn up. [§ 29 ods. 3](law:sk/2002/431#paragraf-29.odsek-3)
  allows tangible assets other than stock and cash to be verified at a longer
  interval of at most four years; cash must always be verified as at the
  statement date.
- **How.** Under [§ 30 ods. 1](law:sk/2002/431#paragraf-30.odsek-1) the actual
  state is established by a **fyzická inventúra** (physical count) for assets
  of a tangible or intangible nature, and by a **dokladová inventúra**
  (verification from documents) for liabilities, for the difference between
  assets and liabilities (equity), and for assets that cannot be counted —
  combining the two where possible.
- **The inventúrny súpis** must contain the particulars listed in
  [§ 30 ods. 2](law:sk/2002/431#paragraf-30.odsek-2), among them the three
  dates — *deň začatia inventúry, deň, ku ktorému bola inventúra vykonaná, a
  deň skončenia inventúry* (písm. b) — the state of the assets *s uvedením
  jednotiek množstva a ceny* (písm. c), the place where they are kept
  (písm. d), the name and signature of the *hmotne zodpovedná osoba*
  (písm. e), the names and signatures of the persons responsible for
  establishing the actual state (písm. i) and notes (písm. j).
- **The inventarizačný zápis** must contain, under
  [§ 30 ods. 3](law:sk/2002/431#paragraf-30.odsek-3), the entity's name and
  seat, the results of comparing the actual state with the books, the results
  of assessing whether the valuation is real (*posúdenie reálnosti ocenenia*,
  [§ 26](law:sk/2002/431#paragraf-26) and 27), and the names and signatures
  of the persons responsible for the inventarizácia.
- **Counting before or after the statement date.**
  [§ 30 ods. 4](law:sk/2002/431#paragraf-30.odsek-4) allows a physical count
  of tangible assets in the last three months of the period or the first month
  of the next (stock at any time in the period), provided the result is rolled
  forward or back to the statement date by the movements in between.
- **Differences.** A shortfall is a *manko* (*schodok* for cash), a surplus a
  *prebytok* ([§ 30 ods. 5](law:sk/2002/431#paragraf-30.odsek-5)); they are
  booked in the period being verified
  ([§ 30 ods. 7](law:sk/2002/431#paragraf-30.odsek-7)).

## Setting it up {#setup}

Nothing to configure. The documents are numbered `INV/<year>/001`,
`INV/<year>/002`, … from one sequence shared by all companies; the year is the
year the document is created, not the year being verified.

The menu is *Accounting → Accounting → Inventarizácia*. On Community the app
is called *Invoicing*, and the *Accounting* submenu is shown only to users with
access to the full accounting features. Invoicing users may create and edit
inventarizácie; only accounting managers may delete them.

## Carrying out an inventarizácia {#usage}

1. **Create the inventarizácia.** *Inventarizácia → New*, then fill the
   three dates under **Termíny (§ 30 ods. 2)**: *Deň začatia inventúry*,
   *Deň, ku ktorému bola inventúra vykonaná* (normally the balance-sheet date)
   and *Deň skončenia inventúry*. The end date may not precede the start date.
   Click **Začať** to move it from *Návrh* to *Prebieha*.
2. **Add the súpisy** on the tab **Inventúrne súpisy**, one per count
   sheet — one per warehouse, cash desk, asset group or account. *Add a line*
   opens the súpis in its own window; for each:
   - *Názov* (*Name*) and *Druh inventarizácie*: **Fyzická inventúra** or
     **Dokladová inventúra**;
   - *Účet* — for a dokladová inventúra, the account whose balance is
     verified; for a fyzická inventúra, the account the assets are kept on
     (used when the difference is booked);
   - *Miesto uloženia majetku*, *Hmotne zodpovedná osoba* (a contact) and
     *Skutočný stav zistil* (a user — the person who established the actual
     state).
3. **Enter the items** (*Položky*) in the same window: *Popis*, optionally
   *Produkt*, *Množstvo*, *Jednotka* (free text) and *Cena za jednotku*. The
   *Hodnota* is quantity × unit price, and the súpis's *Skutočný stav* is the
   sum of its items. Choosing a product fills nothing in; type the price
   yourself. Click a súpis in the list to open it again.
4. **Book state.**
   - *Dokladová inventúra* with an account: *Účtovný stav* is the account's
     balance from **posted** entries dated up to and including the *deň, ku
     ktorému*. It is recalculated when the account, that date or the items
     change. Entries posted later are picked up by **Načítať zostatok účtu**
     in the súpis, or **Načítať účtovné stavy** at the top of the
     inventarizácia for every dokladová inventúra at once.
   - *Fyzická inventúra*: type the *Účtovný stav* from your stock or asset
     records.

   *Rozdiel* is *Skutočný stav* − *Účtovný stav*, per súpis and in total.
5. **Write the zápis** on the tab **Inventarizačný zápis (§ 30 ods. 3)**:
   *Výsledky porovnania skutočného a účtovného stavu*, *Posúdenie reálnosti
   ocenenia* and *Zodpovedný za vykonanie inventarizácie* (§ 30 ods. 3
   písm. d)).
6. Click **Ukončiť**. It is refused when the inventarizácia has no súpis, or
   when any súpis lacks *Skutočný stav zistil* (§ 30 ods. 2 písm. i).
   **Späť na návrh** reopens it at any stage.

### Signs on accounts verified from documents {#signs}

The book balance is debit minus credit, so liability and equity accounts come
out **negative**: a supplier balance of 500 on account 321 reads −500. Enter
the confirmed amounts of such an account with a negative unit price (for
example, quantity 1, price −500) so that *Rozdiel* compares like with like.

## Booking the differences {#differences}

The tab **Inventarizačné rozdiely (§ 30 ods. 5 až 7)** turns the differences of the súpisy into a journal entry.

1. **Give each súpis its account.** *Účet* on a súpis is the account the counted assets are kept on (211 for a cash desk, 132 for goods). On a dokladová inventúra it is already there; on a fyzická inventúra fill it in, because the proposal starts from it.
2. Click **Navrhnúť vyúčtovanie rozdielov**. For every súpis whose difference is not explained yet, one line appears: *Manko / schodok* when the actual state is lower than the books, *Prebytok* when it is higher, for the whole amount, with the accounts proposed (see the table below).
3. **Adjust the lines.** Split a manko into the part within your norm of natural loss (*Úbytok do normy*) and the part above it. Add a line *Náhrada od zodpovednej osoby* for what the liable person is asked to pay, and fill *Partner*. Change either account where your chart or your case differs. The amounts are always positive: the kind carries the direction. *Zostáva vyúčtovať* on each súpis shows what the lines do not explain yet.
4. **A difference that is not booked from here** (a fixed asset retired in the asset register, stock adjusted in Odoo Inventory, a difference explained by a document of its own): tick *Rozdiel sa tu neúčtuje* on the súpis and state the reason. The reason is printed in the zápis.
5. Click **Zaúčtovať rozdiely**. It is offered once every difference is either explained in full or marked as not booked here. One journal entry is created **in draft**, in the *Denník pre rozdiely* (the first miscellaneous journal unless you choose another), dated the *deň, ku ktorému bola inventúra vykonaná*, with the number of the inventarizácia as its reference. The accountant reviews and posts it in Accounting; the button *Účtovné zápisy* at the top opens it.

The status *Rozdiely* in the summary reads *Na vyúčtovanie*, *Pripravené na zaúčtovanie*, *Zápis v návrhu* or *Zaúčtované*.

### Proposed accounts {#difference-accounts}

The proposals follow the accounting procedures for double-entry bookkeeping ([opatrenie MF SR č. 23054/2002-92](law:sk/2002/740)). They are proposals: both accounts stay editable.

| Súpis kept on | Manko / schodok | Úbytok do normy | Prebytok |
|---|---|---|---|
| 211, 213 (cash, ceniny) | 335 / 21x — § 11 ods. 1 písm. b): the schodok is booked as a receivable from the hmotne zodpovedná osoba, not as an expense | — | 21x / 668 |
| 112, 132 and the other accounts of groups 11 and 13 | 549 / 1xx (§ 43 ods. 2 písm. d), § 68 ods. 8) | 501 / 11x, 504 / 13x | 1xx / 648 |
| 121–124 (own production) | 549 / 12x (§ 43 ods. 3 písm. b)) | 61x / 12x | 12x / 61x |
| 01x, 02x (depreciated fixed assets) | none proposed | — | 0xx / 384 (§ 21 ods. 2) |
| 03x (fixed assets not depreciated) | 549 / 03x | — | 03x / 648 (§ 11 ods. 4) |
| anything else (receivables, payables, equity) | none proposed | — | none proposed |

*Náhrada od zodpovednej osoby* proposes 378 / 648 (§ 55 ods. 9 písm. a)).

Where nothing is proposed, the entry is refused until you choose the counterpart yourself. Three cases need more than this entry:

- **Fixed assets.** A manko of a depreciated asset takes the residual value through the accumulated depreciation (§ 36 ods. 4 písm. e)), and a newly found asset must be registered at its fair value. Do both in the asset register and mark the súpis as not booked here; a line on a class 0 account carries a warning.
- **Stock valued by Odoo Inventory.** If Odoo keeps the stock account by itself, correct the quantity in Inventory, which books the difference. A line on such an account carries a warning, because the difference would otherwise be booked twice.
- **Way B of stock accounting.** The year-end stock is booked from the inventarizácia (112 / 501, 132 / 504), so a manko is a reclassification: put 501 or 504 as *Účet* and 549 as the counterpart.

A prebytok of purchased stock caused by a provably wrong issue is credited to group 50 instead of 648 (§ 11 ods. 2); change the counterpart.

The entry carries no VAT and no income-tax adjustment. A manko above the compensation received is not a tax expense ([§ 21 ods. 2 písm. e)](law:sk/2003/595#paragraf-21.odsek-2.pismeno-e) of the Income Tax Act), and VAT deducted on stolen goods is paid back under [§ 53 ods. 5](law:sk/2004/222#paragraf-53.odsek-5) of the VAT Act (549 / 343); both remain with the accountant.

### Taking the booking back {#difference-reversal}

**Zrušiť zaúčtovanie rozdielov** deletes the entry while it is still a draft and reverses it once posted. The reversal is dated the same day as the entry, so it stays in the period verified. **Späť na návrh** on the inventarizácia does the same before it reopens the document, because the súpisy are about to change. The settlement lines stay and can be booked again.

Lines from which an entry was created cannot be changed or deleted until the booking is taken back, and neither can their súpis or the inventarizácia. If a súpis changes after the booking, a warning at the top says the booked amounts no longer match.

**Locked periods.** Differences belong to the period verified ([§ 30 ods. 7](law:sk/2002/431#paragraf-30.odsek-7)). Odoo by itself moves an entry dated in a locked period to the first open day when it is posted. For these entries the module refuses instead: creating, posting and reversing all stop with a message until the period is unlocked.

## Printouts {#reports}

From an inventarizácia, *Print → Inventarizačný zápis* produces the zápis: the
entity's name and seat, the as-of date, a table of every súpis with book state, actual
state and difference and their totals, the comparison text, the valuation
assessment (or *Neuvedené*), and signature lines for the person responsible
for the inventarizácia and for the entity.

**Tlačiť inventúrne súpisy** at the top of the inventarizácia prints its
súpisy, one per page: the entity's name and seat, the three dates, the
type, place and account, the items with quantity, unit, unit price and value,
the totals, notes, and signature lines for the *hmotne zodpovedná osoba* and
the person who established the actual state.

The seat is the company's address; for a natural person keep the residence
there, and the place of business too where it differs.

Signatures are blank lines to be signed on paper; nothing is signed
electronically.

## Limitations {#limitations}

- The súpis has no separate fields for the list of liabilities, the list of
  the equity balances or the recommendations on valuation (§ 30 ods. 2
  písm. f–h). Use the items and *Poznámky*.
- *Zodpovedný za vykonanie inventarizácie* holds one user; § 30 ods. 3
  písm. d) speaks of the person or persons responsible, and the field is not
  required to close.
- For a dokladová inventúra a typed-over book balance does not last: the next
  recalculation or refresh replaces it.
- On a fyzická inventúra nothing is read from Odoo Inventory or the asset
  register; the book state is typed.
- Nothing checks the § 29 ods. 3 or § 30 ods. 4 time windows, and a closed
  inventarizácia stays editable — *Ukončená* locks nothing.
- Adjustments to valuation (opravné položky, § 26 and 27) are not booked; the
  accountant enters them from the zápis.
- The booking of differences does not retire or register fixed assets, does
  not adjust quantities in Odoo Inventory, and books no VAT; see
  [Booking the differences](#differences).
- The entry of differences is in the company currency only, and closing the
  inventarizácia does not require the differences to be booked.
- The asset protocols (*zaraďovací* / *vyraďovací*) are not part of this module: they are in [module:l10n_sk_asset_protocol_base](module:l10n_sk_asset_protocol_base), which needs the asset register.
