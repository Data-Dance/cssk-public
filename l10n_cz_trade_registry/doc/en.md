---
title: CZ Register Extract (§ 435, status, activities)
summary: Keeps a Czech subject's entry in the public register as data, composes the statement § 435 občanského zákoníku requires on your documents from it, and warns about partners the register no longer shows as active.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A Czech business has to state on its documents which register it is entered
in and under which oddíl and vložka. Odoo's Czech localization gives the
company a single free-text field, **Trade Registry**, for that statement. It
is typed once and then forgotten — and goes on being printed after the seat,
and with it the court, has changed.

This module:

- keeps the three coordinates — **Rejstřík** (the register), **Rejstříkový
  soud** (the court keeping it) and **Spisová značka** (oddíl and vložka) — as
  separate fields, on your company and on any contact;
- composes the statement from them, in correct Czech, and keeps the company's
  **Trade Registry** in step, so that it is printed on invoices;
- shows on each Czech contact what the register says about it: status, dates
  of establishment and dissolution, předmět podnikání and činnosti (scope of
  business), and previous names and seats;
- warns on an invoice or bill when the register shows the partner as
  dissolved, historical or suspended.

The data is typed by hand or filled from ARES by
[module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz).

## Legal background {#legal}

[§ 435 odst. 1 občanského zákoníku](law:cz/2012/89#p435) requires every
entrepreneur to state the name and seat on business documents (*obchodní
listiny*) and in information made available to the public by remote access —
a website. Beyond that:

- an entrepreneur entered in the **obchodní rejstřík** states that entry
  **including the oddíl and vložka**;
- one entered in another public register (*veřejný rejstřík*) states the
  entry in that register;
- one entered in no public register states the entry in another evidence —
  for a sole trader, the živnostenský rejstřík;
- an identifying number (IČO), if one was assigned, is stated too.

The public registers are six — obchodní rejstřík, spolkový rejstřík, nadační
rejstřík, rejstřík ústavů, rejstřík společenství vlastníků jednotek and
rejstřík obecně prospěšných společností (§ 1 of zákon č. 304/2013 Sb.) — and
each is kept by a rejstříkový soud: the Městský soud v Praze or a krajský
soud.

## Setting it up {#setup}

*Settings → Companies*, open your Czech company. Above **Trade Registry** are
three new fields:

| Field | Example |
|---|---|
| Rejstřík | Obchodní rejstřík |
| Rejstříkový soud | Městský soud v Praze |
| Spisová značka | C 12345 — oddíl and vložka as the register writes them |

From them the module composes the statement and writes it into **Trade
Registry**, which Odoo's Czech localization prints on invoices:

> Obchodní rejstřík vedený Městským soudem v Praze, oddíl C, vložka 12345

- The statement names the register and the court keeping it rather than
  saying *zapsaná* or *zapsaný*, so it is correct whatever the legal form.
- The court is put in the instrumental (*Městský soud* → *Městským soudem*,
  *Krajský soud* → *Krajským soudem*). The *vedený … soudem* and *oddíl /
  vložka* wording is used only for the six public registers.
- Any other register is written as entered, with the authority after a comma
  and the number as *číslo zápisu: …*. A sole trader who enters only
  *Živnostenský rejstřík* gets just that.
- A number that is not an oddíl and a vložka is printed whole, as *spisová
  značka …*.

**Your own wording wins.** If you type something else into **Trade Registry**,
the module leaves it alone from then on. The composed statement is also shown,
editable, as **§ 435 statement** on the contact behind the company; an edit
there reaches **Trade Registry** too and sticks until a coordinate changes
again. Clearing all three coordinates clears the statement the module wrote.

## The register on a contact {#partner}

Tab **Register (CZ)** on a contact in Czechia (or with no country):

| Group | Fields |
|---|---|
| Zápis | Rejstřík, Rejstříkový soud, Spisová značka, Datum vzniku, § 435 statement |
| Stav | Stav v rejstříku, Datum zániku, Register checked (when the register was last read) |

Below them, filled from the register and read-only:

- **Předmět podnikání a činnosti** — what the entry says the subject does
  (předmět podnikání, předmět činnosti, doplňková činnost, účel), each with
  the day it was entered and the day it was deleted. These are the entry's own
  words, not the statistical CZ-NACE code.
- **Předchozí názvy a sídla** — previous names and registered seats with their
  validity, useful for matching an old document to today's partner.

With [module:partner_autocomplete_ares_cz](module:partner_autocomplete_ares_cz)
installed, picking a company from the ARES suggestions or running *Actions →
Update* on the contact fills all of it; nothing needs setting up. A sole trader
who is in no public register but is in the živnostenský rejstřík gets
*Živnostenský rejstřík* as the register.

## Partners that are no longer active {#dissolved}

When **Stav v rejstříku** is *Zaniklý*, *Historický* or *Pozastavený*:

- a yellow banner at the top of the contact says the subject is not active,
  with the date of dissolution if known; the status can be shown as a column
  in the contact list;
- an invoice, credit note or receipt of a company whose fiscal country is
  Czechia shows a warning naming the status, the date and when it was checked
  in the register. On a vendor bill it adds that the supplier may not have
  existed at the time of supply, so the right to deduct VAT should be checked;
- when such a document is posted, the warning is also written to its chatter.

The warning never blocks posting. A final invoice or a late bill from a
wound-up partner can be perfectly legitimate; the date on the document
decides, and only a person can judge that.

To see every such partner at once, open *Accounting → Customers → Neaktivní
subjekty (CZ)*, or use the filter **Neaktivní subjekty (CZ)** in any contact
list — customers, vendors or contacts.

## Limitations {#limitations}

- Odoo's Czech localization prints **Trade Registry** on invoices only, under
  the label *Trade registry:* (in Czech *Zápis v obchodním rejstříku:*), also
  when the statement names another register. § 435 also covers orders,
  letters and the website; put the statement there yourself.
- The statement is deliberately not the usual *zapsaná v obchodním rejstříku
  vedeném …*. If you prefer that wording, type it into **Trade Registry**.
- Only *Městský soud* and *Krajský soud* are declined. Anything else is
  printed as entered, which may read stiffly. Check the statement once.
- There is no list of filed financial statements: they are in the sbírka
  listin, which ARES does not provide.
- The status is as current as the last lookup; nothing refreshes it on a
  schedule. Without the ARES module the status, dates and lists stay empty
  unless you enter them by hand.
