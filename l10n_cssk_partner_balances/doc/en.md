---
title: CZ/SK Partner Balance Confirmation and Set-off (Saldokonto, Zápočet)
summary: Balance confirmations of a partner's open receivables and payables as of a date, with a PDF to countersign, and set-off agreements that clear mutual receivables and payables in the books.
verified: 19.0.1.2.1
---

## What it is for {#purpose}

Two everyday documents of Czech and Slovak bookkeeping around open partner
balances (*saldokonto*):

1. **Balance confirmation** (*odsúhlasenie zostatkov* / *odsouhlasení
   zůstatků*). A stored document listing a partner's open receivables and
   payables as they stood on a chosen date, which you print, send to the
   partner and mark as agreed or disputed. It is typically used at the year
   end to support the inventory of receivables and payables.
2. **Set-off** (*zápočet*). An agreement or a one-sided declaration that
   offsets what the partner owes you against what you owe the partner. On
   posting it creates the clearing journal entry and reconciles the invoices.

The module needs only Odoo's `account` and [module:l10n_cssk_core](module:l10n_cssk_core),
so it works in Community and Enterprise. It is available to users with
*Show Full Accounting Features* or the accounting *Administrator* right;
only an Administrator can delete records.

## Legal background {#legal}

**Inventory.** Neither accounting act requires a confirmation from the
partner, but both require the company to verify its receivables and payables
at the balance-sheet date, and for these the actual state is established by a
documentary inventory (*dokladová inventúra* / *dokladová inventura*):

- **Slovakia:** [§ 29 ods. 1 and 2](law:sk/2002/431#paragraf-29.odsek-1) and
  [§ 30 ods. 1](law:sk/2002/431#paragraf-30.odsek-1) of the Accounting Act —
  the inventory verifies that the books correspond to reality, is carried out
  as at the day the financial statements are prepared, and liabilities, and
  assets that cannot be counted physically, are inventoried by documents.
- **Czech Republic:** [§ 29 odst. 1 and § 30 odst. 1 písm. b) of the
  Accounting Act](law:cz/1991/563) — periodic inventory as at the moment the
  financial statements are prepared, liabilities and assets that cannot be
  seen are inventoried by documents.

A balance confirmation signed by the partner is a common piece of evidence for
that documentary inventory.

**Set-off.**

- **Slovakia:** under [§ 580 of the Civil Code](law:sk/1964/40#paragraf-580)
  mutual claims of the same kind extinguish by set-off to the extent they
  cover each other, once one party makes a declaration aimed at set-off; they
  extinguish *"okamihom, keď sa stretli pohľadávky spôsobilé na započítanie"*.
  [§ 581 ods. 2](law:sk/1964/40#paragraf-581.odsek-2) excludes, among others,
  time-barred claims and setting off a claim not yet due against a due one;
  [§ 581 ods. 3](law:sk/1964/40#paragraf-581.odsek-3) lets the parties set off
  even such claims by agreement. Between businesses the Commercial Code adds
  that only claims enforceable in court qualify
  ([§ 358](law:sk/1991/513#paragraf-358)), that a claim not yet due cannot be
  set off against a due one unless the debtor is unable to pay
  ([§ 359](law:sk/1991/513#paragraf-359)), and that claims in different
  currencies can be set off only when they are freely convertible, at the rate
  of the day they became capable of set-off ([§ 362](law:sk/1991/513#paragraf-362)).
- **Czech Republic:** under [§ 1982 of the Civil Code](law:cz/2012/89) either
  party may declare a set-off of mutual claims of the same kind once it may
  demand its own claim and perform its own debt; the claims extinguish to the
  extent they cover each other, with effect from the moment both became
  capable of set-off. [§ 1987](law:cz/2012/89) admits only claims enforceable
  in court and not uncertain, and [§ 1991](law:cz/2012/89) lets the parties
  agree a set-off that a one-sided declaration could not achieve.

That is the difference between the two modes of the module: a **bilateral
agreement** (*dohoda o vzájomnom započítaní* / *dohoda o započtení*), signed by
both parties, and a **unilateral set-off** (*jednostranné započítanie* /
*jednostranné započtení*), a declaration delivered to the other party, usable
only where the claims meet the statutory conditions. The module does not check
those conditions for you.

## Balance confirmations {#confirmation}

*Accounting → Customers → Balance Confirmations*, then *New*:

| Field | Meaning |
|---|---|
| Partner | The company (not a contact person). Open items of all its contacts are included. |
| Contact | The person the confirmation is addressed to. |
| As Of Date | The date the balance is confirmed for, typically 31 December. |
| Confirmation Type | *Receivables only*, *Payables only*, or *Receivables and payables*. |

Click **Compute**. The *Open items* tab is filled with every posted item on a
receivable or payable account of the partner that was open **on the as-of
date**: a payment or reconciliation dated after that date is added back, so a
31 December confirmation prepared in February still shows an invoice paid in
January, at its full open amount on 31 December. *Total Receivable*, *Total
Payable* and *Net Balance* (positive = the partner owes you) are computed from
the lines.

The lines are a **snapshot**: they keep their own copy of the document
number, dates and amount, so the confirmation stays as it was sent even when
the ledger changes later. Click **Compute** again to rebuild it, which is
possible while it is in *Draft* or *Sent*.

The workflow:

1. **Print** (shown once the confirmation is not a draft) gives the PDF
   *Balance Confirmation (Saldokonto)* with both companies, the list of items,
   the totals and two signature lines. **Mark Sent** sets the state to
   *Sent*; it does not send an e-mail — send the PDF yourself, for example
   from the chatter.
2. When the partner answers, click **Agreed** or **Disputed**.
3. If the partner disputes individual items, tick **Blocked** on those lines.
   They stay on the PDF, marked *(sporné)* and greyed, but are left out of
   the totals.

**Generate Balance Confirmations** (*Accounting → Customers*) issues them in
bulk: choose the company, the as-of date, the type and optionally the
partners — left empty, every partner with an open item on that date gets one
— and the computed confirmations open in a list.

The PDF is in Czech or Slovak by the company's fiscal country, with English,
and names the parties neutrally (*Company* and *Partner*), since a
confirmation of payables makes your company the debtor.

An agreed or disputed confirmation is frozen: its lines cannot be changed and
the record cannot be deleted, only cancelled. **Reset to Draft** unfreezes it.
Confirmations are numbered `SALDO/<year>/0001`.

## Set-off agreements {#netting}

*Accounting → Vendors → Netting Agreements*, then *New*:

1. Choose the **Partner**, the **Agreement Date**, the **Currency** and the
   **Netting Mode** — *Bilateral agreement* or *Unilateral set-off*.
   Optionally choose the **Clearing Journal**; without one the first
   miscellaneous journal of the company is used.
2. On the tabs **Receivables (pohľadávky)** and **Payables (záväzky)**, add the open journal items to
   offset, and in *Amount To Offset* how much of each. Only posted, open
   receivable and payable items of the agreement's partner can be chosen. A part of an item may
   be offset; the amount cannot exceed the item's open amount.
3. The agreement can be posted only when the receivables total equals the
   payables total (*Is Balanced*); that amount is the *Netting Amount*.

An item goes to the side given by who owes whom, not by the account: an open
customer credit note is a debt you owe the partner and belongs on the
payables side; a supplier credit note belongs on the receivables side.

The workflow differs by mode:

| Mode | Steps |
|---|---|
| Bilateral agreement | Confirm → Mark Sent → Countersigned → Post |
| Unilateral set-off | Confirm → Mark Sent → Post (no countersignature) |

**Create Netting Agreement** (*Accounting → Vendors*) proposes one: choose
the partner, date and currency, and it loads the partner's open items and
allocates the largest balanced amount, oldest items first.

The lines can be changed only in *Draft*. The PDF *Set-off (Zápočet)*, from
the *Print* menu, is titled as an agreement with two signature lines, or as a
notice of unilateral set-off with one.

**Post** first checks that every item is still open for at least the agreed
amount (a payment may have arrived meanwhile), then creates a journal entry
dated with the agreement date that credits each receivable and debits each
payable by its amount to offset, and reconciles each item with its own
clearing line, so partial offsets are kept exactly. Agreements are numbered
`ZAP/<year>/0001`.

**Foreign currency.** In the company's currency any open item can be offset,
at its booked amount. In a foreign currency only items in that currency can
be offset; amounts are in that currency, the clearing entry is booked at the
rate of the agreement date, and the difference to each invoice's own rate is
booked as an exchange difference on reconciliation.

**Cancel with reversal** on a posted agreement removes the reconciliations and
reverses the clearing entry, so every item is open again exactly as before. A
posted agreement cannot be deleted.

## Limitations {#limitations}

- The module does not check the legal conditions of a unilateral set-off
  (maturity, enforceability, exclusions) or the partner's agreement; you do.
- The clearing entry is dated with the agreement date and, in a foreign
  currency, booked at that day's rate. The claims themselves extinguish as of
  the moment they became capable of set-off (§ 580 of the Slovak and § 1982
  of the Czech Civil Code), which the PDF states; if your accountant wants the
  entry on that day, set the agreement date to it.
- Both PDFs follow the company's fiscal country — Czech wording and DIČ for a
  Czech company, Slovak wording and IČ DPH otherwise — with English beside it.
  Have the wording checked before the first use.
- The confirmation PDF shows amounts in the company currency only.
- *Mark Sent* only changes the state; nothing is e-mailed.
