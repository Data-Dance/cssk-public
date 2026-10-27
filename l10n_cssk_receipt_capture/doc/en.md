---
title: Fiscal Receipt Capture (bločky / účtenky)
summary: Captures cash-register receipts from a QR code, a photograph or an expense upload, checks that their figures add up, and turns them into a draft vendor receipt or an employee expense with the VAT split by rate.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Fuel, meals, small purchases: a business collects many till receipts
(*bločky* in Slovakia, *účtenky* in Czechia), and each has to be booked with
its VAT split by rate. This module is the common frame for that. It holds the
**captured receipt** — seller, date, total, items and the per-rate VAT recap
— and turns it into Odoo documents, while separate **capture providers**
supply the data:

| Provider | Module | Reads |
|---|---|---|
| eKasa lookup | [module:l10n_sk_ekasa_receipt](module:l10n_sk_ekasa_receipt) | the QR code of a Slovak receipt; the seller's registered receipt, items and all, is fetched from the Finančná správa service |
| AI reader | [module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai) | the photograph, with a language model — for Czech and foreign receipts, and Slovak ones whose code cannot be read (see [AI reader](#ai-reader)) |

A receipt that reads cleanly becomes a **draft vendor receipt** (Odoo's
*Purchase Receipt*) or, with
[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense),
an **employee expense** (see [Expenses](#expenses)). A receipt whose figures
do not add up is parked for review, never rounded into place.

The VAT recap is kept as its own table because it is the only trustworthy
source and a receipt may carry three rates (a Slovak restaurant bill: food,
soft drinks, alcohol). Item quantities are kept on the receipt but posted as
quantity 1 at the line total, since a unit price rounded to cents would not
foot (31.17 l of fuel for 57.85 € is not 1.86 € × 31.17).

## Legal background {#legal}

- **When a receipt is enough to deduct VAT.** A till receipt is a simplified
  tax document only up to a limit; above it the buyer needs a full invoice.
  - Slovakia: a document issued by a *pokladnica e-kasa klient* is a
    simplified invoice *"ak cena tovaru alebo služby vrátane dane nie je viac
    ako 400 eur"* —
    [§ 74 ods. 3 písm. b) of the VAT Act](law:sk/2004/222#paragraf-74.odsek-3.pismeno-b);
    the deduction requires an invoice —
    [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a).
  - Czechia: a *zjednodušený daňový doklad* may be issued only *"pokud
    celková částka za plnění na daňovém dokladu není vyšší než 10000 Kč"* —
    [§ 30 odst. 1 of the VAT Act No. 235/2004 Sb.](law:cz/2004/235).
- **The eKasa lookup.** Under
  [§ 18 ods. 1 of Act No. 384/2025 Z. z.](law:sk/2025/384#paragraf-18.odsek-1)
  the Financial Directorate lets anyone verify, through the QR code or the
  receipt identifier, the data of receipts sent to the eKasa system and makes
  them available, repeatedly. A verifier (*overovateľ*,
  [§ 2 ods. 1 písm. aj)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-aj)) must
  first notify the Financial Directorate of the IP address it calls from and
  must send truthful verification results —
  [§ 18 ods. 11](law:sk/2025/384#paragraf-18.odsek-11). The eKasa module
  refuses lookups until that notification is confirmed in its settings.

## What is sent, when, and by whom {#data}

| Where | What | Provider |
|---|---|---|
| Finančná správa (eKasa) | the QR code text, or identifiers printed on the receipt | eKasa lookup |
| your model provider, or Data Dance's extraction service through the broker | the photograph or PDF of the receipt | AI reader |
| the public company registers | the seller's IČO, to confirm its name | AI reader |

A reading starts when:

- someone with Invoicing rights presses **Capture** on a receipt (*New*,
  *Error* or *Needs Review*);
- **any employee** scans a QR code with **Scan Receipt** (the camera is read
  in the browser; only the decoded text reaches the server);
- **any employee** uploads receipt images in the Expenses app while *Capture
  on Expense Upload* is on (the default) — one reading per image, run with
  superuser rights so that employees need no access to accounting;
- a reading failed for a **temporary** reason (service busy or unreachable):
  it is retried automatically after 15 minutes, 1 hour and 4 hours. A refusal,
  an unknown receipt or an unreadable photograph is never retried on a timer.

Providers are tried in their order, code readers first: with the eKasa
lookup enabled, a Slovak receipt with a readable QR code never reaches the
model. Every attempt is logged on the
receipt (**Attempts**) with its outcome, duration and, for the AI reader,
tokens and cost.

## Setting it up {#setup}

*Accounting → Configuration → Settings*, block **Fiscal Receipt Capture**
(labels in English; the module has no Czech or Slovak catalogue yet):

| Setting | Purpose |
|---|---|
| Receipt Journal | purchase journal for vendor receipts; empty uses the first one |
| Default Expense Account | account of every line; **required** before a vendor receipt can be created |
| Document Detail | *One line per VAT rate* (default — posts exactly the base the seller reported) or *One line per receipt item* |
| Auto-create Seller | currently has no effect: sellers are created with the **Create Seller** button |
| Receipts: AI Model Chain | with the AI reader, see [below](#ai-reader) |

The purchase tax for each VAT rate is taken from the VAT-rate mapping of
[module:account_invoice_ai_extract](module:account_invoice_ai_extract) when
installed, else the company's default purchase tax or a domestic purchase tax
of that rate. A mapping that points a rate at a tax of another rate is
refused.

*Accounting → Configuration → Accounting → Capture Providers* (managers)
lists the providers with their order, countries and an *Active* switch.

To read QR codes off photographs, the server needs the Python package
`zxing-cpp`; without it the receipt says so and the camera scan still works.

## Working with receipts {#usage}

*Accounting → Vendors → Fiscal Receipts*:

- **Scan Receipt** — opens the camera; scan the fiscal QR code. A loyalty or
  web link printed next to it is rejected and the scanner stays open.
- **Captured Receipts** — all receipts. *New*, attach the photograph
  (*Source image*) or paste the QR text (*QR payload*), then **Capture**.
- **To Review** — receipts that are new, failed or parked.

States: *New* → *Captured* (everything adds up), *Needs Review* (a check
failed; the reason is shown), *Error* (the source refused or nothing could
read it; the reason is shown) → *Posted* once a document exists.

**Checks before a receipt counts as captured:**

- a total exists, and base plus VAT equals it;
- the items sum to the total;
- every VAT bucket is arithmetically right for its rate, and matches the
  items carrying that rate; no item carries a rate missing from the recap;
- no item is marked as a return or correction (their sign is never guessed);
- for an AI reading, the model's confidence is above zero and not below the
  company's threshold.

A receipt already captured with the same receipt identifier is refused as a
duplicate. **Accept Anyway** moves a parked receipt to *Captured* on your
responsibility; the reported discrepancy is kept in the chatter.

**The seller** is matched by VAT number, then IČO, then tax number — never by
name. **Create Seller** creates a partner from the receipt's name, VAT number
and IČO. The premises where the receipt was issued are kept as a note and do
not reach the partner.

**VAT that may not be deducted.** When the total exceeds the limit above
(400 EUR for a seller with a Slovak VAT number, 10 000 Kč for a Czech one;
by the company's country when the receipt shows no VAT number), the receipt
says so and its VAT is booked as part of the cost. Tick **Full invoice held**
when you have a full invoice for the purchase. A vendor receipt from such a
receipt cannot be posted with VAT on it.

**Create Vendor Receipt** creates a **draft** *Purchase Receipt* dated with
the receipt, referenced by the receipt identifier, with one line per VAT rate
or per item (quantity 1, net amount, the default expense account), and a copy
of the photograph. It is refused when a rate has no purchase tax, when the
mapped tax is price-included, or when the document's total or VAT — in total
or per rate — differs from the receipt. Review and post it as usual.

## AI reader {#ai-reader}

[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
reads a photographed or scanned receipt (an image, or a PDF) with a language
model, through the same connection as
[AI invoice extraction](module:account_invoice_ai_extract#data). It is the
only reader for Czech receipts, which carry no code that can be looked up.

- **What is sent:** the image — re-encoded as PNG if it is BMP or TIFF — or
  the PDF, with fixed instructions for receipts. The model returns the
  seller's identifiers, date, total, items with line totals including VAT,
  the VAT recap, its confidence and notes, and the fiscal identifiers printed
  on a Slovak receipt.
- **Printed identifiers:** when a Slovak QR code could not be decoded, those
  identifiers are tried with the eKasa lookup; if the registered receipt is
  found (and its total matches the photograph), its figures replace the
  reading, otherwise the receipt is parked for review.
- **Seller name from the register:** by the IČO read, through
  [module:l10n_cssk_registry_verify](module:l10n_cssk_registry_verify), when
  the register's VAT number agrees with the one read — or, with no VAT number
  to compare, when the names do not contradict each other. Otherwise the
  reading stands and the chatter says why.
- **Model chain:** *Receipts: AI Model Chain* in the receipt settings — the
  same mechanism as for invoices, usually with a stronger model, since
  thermal paper reads worse than a PDF. Empty uses the default provider and
  model of AI invoice extraction, whose **confidence threshold** also applies.
- The **AI Reading** tab shows the confidence, the model's notes, tokens and
  cost (cost hidden through the broker).

Every reading is a paid call; see [what is sent](#data) for who can start one.

## Expenses {#expenses}

[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense)
connects receipts with Odoo's Expenses app (Community):

- **Create Expenses** on a captured receipt (Invoicing users) creates **one**
  expense for the whole receipt, whatever its VAT rates, for the employee of
  the current user, in the category set under *Expenses → Configuration →
  Settings → Receipt Capture* (*Receipt Expense Category*; empty uses Odoo's
  general expense category). Its total and VAT are checked against the
  receipt.
- **Uploading receipts in Expenses** (*Expenses → My Expenses*, Odoo's
  *Upload* button) — with *Capture on Expense Upload* on, each image becomes a
  receipt and is read; a clean reading fills the expense (amount, taxes,
  vendor), otherwise the expense shows why. A notification sums up how many
  were read, need checking or failed.
- **Scan Receipt** and **My Receipts** appear under *Expenses → My Expenses*;
  an employee sees the receipts they captured and those behind their own
  expenses.
- **Several VAT rates on one expense.** Odoo applies all of an expense's
  taxes to one base, which for 23 % and 5 % would give 28 % on everything.
  For an expense from a receipt, the VAT figure and the journal entry —
  employee-paid or company-paid — are built rate by rate from the receipt's
  recap. Such an expense refuses to post once its amount or taxes are edited
  away from the receipt.
- When the receipt's VAT is not deductible, the expense carries the gross
  amount without tax.
- A receipt claimed as expenses can no longer become a vendor receipt, and
  vice versa.

## Limitations {#limitations}

- The deduction limit is applied by the seller's VAT prefix to every
  receipt: the Slovak 400 EUR rule is written for e-kasa receipts, and the
  general 100 EUR rule of § 74 ods. 3 písm. a) is not applied. For Czech
  receipts the module assumes that a receipt up to 10 000 Kč is a valid
  simplified tax document; it does not check its contents.
- **Auto-create Seller** in the settings does nothing.
- Returns and corrections on a receipt are not posted automatically.
- Item quantities are informative only; every line is quantity 1.
- All lines go to the default expense account; recode fuel, meals and the
  rest afterwards.
- Expense uploads by employees start paid AI readings without an accountant
  in the loop; switch *Capture on Expense Upload* off if that is not wanted.
- The AI reader's figures are a reading of paper: the checks catch figures
  that do not add up, not a total misread consistently everywhere.
