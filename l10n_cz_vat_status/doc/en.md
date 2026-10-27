---
title: CZ VAT Status (plátce / identifikovaná osoba / neplátce)
summary: Records when the Czech company was a VAT payer, an identified person or a non-payer, and taxes every invoice, bill, DPHDP3 and kontrolní hlášení by the status on the document's own date.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

A Czech company is not always a **plátce DPH** (VAT payer). It may start as a
**neplátce** (non-payer), become a plátce when its turnover crosses the
threshold or by voluntary registration, be an **identifikovaná osoba**
(identified person, registered only for cross-border transactions) in
between, and be deregistered again. Each change takes effect on a particular
day, often mid-year.

Without this module the Czech localization treats every Czech company as a
plátce. With it you record the company's status history, and every document
is taxed by the status on its own date:

- a non-payer's invoices carry no VAT and are not presented as a *daňový
  doklad*; its suppliers' VAT becomes part of the cost;
- an identified person self-assesses VAT on intra-Community acquisitions and
  services from abroad, without a deduction, and keeps reporting its services
  to other member states;
- DPHDP3 is filed with the right *typ plátce*, and the kontrolní hlášení
  covers only the days the company was a plátce.

**No history, no change.** Until the company has at least one status row
nothing behaves differently: DPHDP3 says *P*, taxes, the kontrolní hlášení and
the invoice stay as they were, and no new taxes are created.

## Legal background {#legal}

All references are to the [zákon o DPH (235/2004 Sb.)](law:cz/2004/235).

- **Who becomes a plátce.** § 6 odst. 1: from 1 January of the year after
  the year in which the domestic turnover exceeded CZK 2,000,000; § 6 odst. 2:
  from the day after the turnover exceeded CZK 2,536,500 in the current year,
  or the day after the threshold was exceeded if the person chose so in a
  timely registration. § 6f: voluntary plátce from the day after the
  registration decision is notified. § 6g–6i: identifikovaná osoba from the
  day of the first acquisition, receipt or supply that triggers it.
- **Ceasing.** § 107b odst. 3 and 4: a plátce or identifikovaná osoba
  deregistered on request ceases on the day after the decision is notified;
  § 107b odst. 5: a plátce deregistered on request becomes an identifikovaná
  osoba on the day it ceases to be a plátce, if it does not meet the
  conditions for cancelling that registration too or asked for it.
- **Output VAT.** § 108 odst. 1: a plátce must declare VAT on its taxable
  supplies. § 108 odst. 4 písm. g): whoever issues a document stating VAT must
  declare it — which is why the module refuses to post a non-payer's invoice
  with VAT instead of merely warning.
- **What an identifikovaná osoba owes.** § 108 odst. 2: VAT on an
  intra-Community acquisition of goods (plátce or identifikovaná osoba);
  § 108 odst. 3 písm. a): VAT on a service, goods with installation or goods
  through networks supplied by a person not established in the Czech
  Republic. Other goods from such a person (§ 108 odst. 3 písm. b)), the
  domestic reverse charge (§ 108 odst. 4 písm. a)) and import self-assessment
  (písm. c)) name only a plátce; a non-payer pays import VAT to the customs
  office (§ 108 odst. 5 písm. a)).
- **Deduction.** § 72 odst. 1 gives the right to deduct to a plátce only;
  § 72 odst. 5: it arises when the obligation to declare the tax arose.
- **Tax point.** § 20a odst. 1: the obligation to declare VAT arises on the
  day of the taxable supply (DUZP).
- **Filings.** § 101 odst. 1: a plátce and an identifikovaná osoba file a VAT
  return; § 101c: "*Plátce* je povinen podat kontrolní hlášení" — a non-payer
  and an identifikovaná osoba file none.
- **Documents.** § 28 odst. 1: the duty to issue a daňový doklad is a
  plátce's; § 28 odst. 3 extends it to any osoba povinná k dani for a
  cross-border service.

## Setting it up {#setup}

*Settings → Users & Companies → Companies*, open the Czech company, tab **VAT
status** (shown only for companies in the Czech Republic).

1. Add one row per change, oldest first. Each row says "from this day on,
   the company was …" and applies until the day before the next row. Days
   before the first row count as plátce, so if the company started as a
   neplátce, its first row must say so (legal basis *Nikdy nebyl
   registrován*, from its first day).
2. For each row choose the **Legal basis** and enter the **Event date** — the
   day the Act counts from (turnover exceeded, decision notified, decision
   final, first acquisition…). The status and the **Valid from** day are then
   proposed:

   | Legal basis | Status | Valid from |
   |---|---|---|
   | § 6 odst. 1 – obrat překročen, plátce od 1. 1. | plátce | 1 January of the following year |
   | § 6 odst. 2 – obrat překročen, plátce dnem následujícím | plátce | event + 1 day |
   | § 6f / § 94a – dobrovolná registrace (den po oznámení) | plátce | event + 1 day |
   | § 6a–6ea – jiný důvod | plátce | enter by hand |
   | § 6g – první pořízení zboží…, § 6h – přijetí plnění…, § 6i – poskytnutí služby… | identifikovaná osoba | event |
   | § 6j–6l / § 97a – registrace na přihlášku (den po oznámení) | identifikovaná osoba | event + 1 day |
   | § 107b odst. 5 – po zrušení registrace plátce | identifikovaná osoba | event |
   | Nikdy nebyl registrován | neplátce | enter by hand |
   | § 106 odst. 8 písm. a) – zrušení registrace z moci úřední (právní moc) | neplátce | event |
   | § 107b odst. 3 – zrušení registrace na žádost (den po oznámení) | neplátce | event + 1 day |
   | § 106b – zánik registrace plátce | neplátce | event |
   | § 107 odst. 3 – zrušení registrace identifikované osoby z moci úřední (právní moc) | neplátce | event |
   | § 107b odst. 4 – zrušení registrace identifikované osoby na žádost (den po oznámení) | neplátce | event + 1 day |

   For a § 6 plátce the status arises by law on the day shown, whatever the
   date of the registration decision: enter that day, not the decision's.
   The proposal is only a proposal; **Valid from** stays editable. A legal
   basis that does not fit the chosen status is refused.
3. Optionally record the **Č. j. rozhodnutí** (reference of the tax office's
   decision) and a note.

**VAT status today** shows the current status. The two **Invoice statement**
fields hold the sentence printed on a non-payer's and an identified person's
invoices (defaults "Nejsem plátce DPH." and "Nejsem plátce DPH (identifikovaná
osoba)."; a legal entity may prefer "Nejsme plátci DPH."; empty prints
nothing).

As soon as a row with a non-payer status exists, the module creates the
**non-payer variants** of the company's purchase taxes (see
[Taxes](#taxes)). **Regenerate non-payer taxes** creates any that are
missing; it also runs on its own whenever the history changes and before
posting.

Changing the history later re-decides documents already posted: their
kontrolní hlášení section is recomputed from the earliest changed day, and
VAT-deferral entries are withdrawn or created (see [Filings](#filings)).
Returns already filed are not changed — correcting them takes a dodatečné
přiznání.

## Which date decides {#dates}

A document takes the status on its **DUZP** (*Taxable Supply Date*), falling
back to the invoice date and then the accounting date. Both questions the
status answers — does output VAT arise, is input VAT deductible — are tied to
the tax point by § 20a odst. 1 and § 72 odst. 5; the issue date and the
accounting date decide neither.

- **Boundary days.** A row applies from its first day inclusive. A document
  whose DUZP is the first day of a new status falls under the new status; one
  dated the day before, under the old one.
- **Credit notes** take the status of the invoice they correct, even when
  issued after the change.
- On a non-plátce date the document shows **Company VAT status** next to the
  DUZP.

## What happens to taxes {#taxes}

Taxes are recognised by the DPHDP3 row their base is reported on (the *VAT
<n> Base* tags of the Czech chart), so taxes you add yourself are handled the
same way as long as they carry the chart's tags.

| Tax (DPHDP3 row of its base) | plátce | identifikovaná osoba | neplátce |
|---|---|---|---|
| Sales: domestic, export, other taxed sales | as is | **removed** | **removed** |
| Sales: § 9 odst. 1 service to another member state (ř. 21), triangular trade (ř. 31) | as is | as is | **removed** |
| Purchases: domestic with deduction (ř. 40/41 and other deductible taxes) | as is | **no deduction**, VAT to cost | **no deduction**, VAT to cost |
| Purchases: domestic reverse charge § 92a (ř. 10/11) | as is | **no deduction**, VAT to cost | **no deduction**, VAT to cost |
| Purchases: EU goods, EU and foreign services, other self-assessed (ř. 3–6, 12, 13) | as is | **self-assessed, no deduction** | **removed** |
| Purchases: import (ř. 7/8, 32, 42) | as is | **removed** | **removed** |
| Purchases: new means of transport (ř. 9) | as is | as is | as is |

The variants are copies of the source tax, named after it with the suffix
*(no deduction)* or *(identified person)*, and linked to it (field **Plátce
tax** on the tax form):

- **No deduction** — a single tax line with no account and no tags. Odoo
  posts it onto the expense account of the bill line, so the VAT becomes part
  of the cost; nothing reaches account 343 or the return.
- **Self-assessed, no deduction** — the liability side and its output tags
  (ř. 3–6, 12, 13) stay as on the plátce tax; the deduction side loses its
  account and lands on the cost, and every deduction tag (ř. 40–53) is
  removed. DPHDP3 shows the output tax and no deduction.

Taxes are applied automatically when lines are created from a product or
account, and again when you change the DUZP or invoice date of a draft
across a status boundary — in both directions, so moving the date back
restores the plátce taxes.

**Posting is refused** when an invoice's taxes do not fit the status on its
DUZP. A draft with such lines shows a warning with the button **Apply VAT
status taxes**, which replaces them. A purchase tax whose repartition does
not have the shape of the Czech chart (one +100 % and one −100 % tax line)
gets no identified-person variant; a bill using it on an identified-person
date cannot be posted until you set the tax by hand.

## On the invoice {#invoice}

A customer invoice dated while the company is not a plátce:

- carries no VAT (the taxes were removed);
- does not print the **DUZP** — the one element that exists only because of
  VAT. Odoo's title "Invoice" (Faktura) claims nothing and is left as it is;
- prints the **Invoice statement** below the notes.

The exception is an identified person's § 9 odst. 1 service to another
member state, which § 28 odst. 3 requires to be documented by a daňový
doklad: such an invoice keeps its DUZP. The identified-person statement is
printed on it too.

## Filings {#filings}

- **DPHDP3.** *typ plátce* is taken from the status on the **last day** of
  the return's period: *P* plátce, *I* identifikovaná osoba, *N* neplátce.
  Each document in the period was taxed by the status on its own DUZP. When
  the status changes within the period, the return says so in its chatter
  when computed; whether the change needs a separate filing for part of the
  period is for you and the tax office to decide.
- **Kontrolní hlášení.** Only documents dated on plátce days are included.
  A period with no plátce day cannot be computed at all; the message tells
  you to answer a tax-office request (*výzva*) with "B – Nemám povinnost
  podat KH". A period with a change is computed from the plátce days, and the
  statement's chatter lists the segments.
- **Souhrnné hlášení.** An identified person's § 9 odst. 1 services keep
  their tax, so the EC sales list reports them as for a plátce.
- **VAT period declared** (the later deduction period from
  [module:l10n_cssk_core](module:l10n_cssk_core)). It exists for a plátce
  who claims a deduction later than it arose. On a document dated while the
  company was not a plátce it is **ignored**: the document is reported in
  the period of its tax point, and its VAT is not moved off account 343 by
  deferral entries. The form says so in a blue note. If a history change
  should withdraw or create deferral entries in a locked period, the
  document gets a chatter message and the entries are left for you to
  correct.

## Sales and purchase orders {#orders}

Two bridge modules install themselves when Sales or Purchase is installed:

- [module:l10n_cz_vat_status_sale](module:l10n_cz_vat_status_sale) — sales
  order lines;
- [module:l10n_cz_vat_status_purchase](module:l10n_cz_vat_status_purchase)
  — purchase order lines, including lines created by reordering rules and
  make-to-order.

They propose the taxes the status allows on the **order date**. An order has
no tax point, so this is only a proposal: the invoice or bill made from it is
decided again by its own DUZP and cannot be posted with taxes that no longer
fit. An order confirmed in June and invoiced in July across a registration
gets its taxes corrected on the invoice.

## Limitations {#limitations}

- **Adjustments on a status change** are not made: the deduction of VAT on
  stock and assets when becoming a plátce, and the corrections and payments
  due on deregistration. Book them by hand.
- **The turnover threshold is not monitored.** The status is what you
  record.
- **Skupina** (group registration, *typ plátce S*) and **nový dopravní
  prostředek** (*R*, *D*) are not modelled; ř. 9 taxes are left alone.
- **Import VAT paid to customs** by a non-payer is not booked: the import
  taxes are removed from the bill, and the VAT the customs office assesses is
  booked from the customs document as a cost.
- **Advance invoices** made by other modules are not stopped; a non-payer
  should not issue them.
- **OSS and the EU small-business scheme** are not statuses of this module.
- **Imports** of historical documents can skip the posting check with the
  technical context key `l10n_cz_vat_status_skip_check`; nothing in the user
  interface sets it.
- **Open questions** for your tax adviser, where the module takes a default:
  ř. 12/13 taxes are treated as owed by an identified person, although they
  also cover § 108 odst. 3 písm. b) goods, which only a plátce owes; an
  intra-Community acquisition is decided by the DUZP on the bill, not by the
  § 25 tax point; a credit note after deregistration takes the status of the
  original invoice; a plátce's own self-assessment with a later declared
  period still moves the liability together with the deduction.
