---
title: SK Register Extract (§ 3a, status, activities, filings)
summary: Keeps a Slovak subject's register entry as data, composes the § 3a Obchodného zákonníka statement for your documents from it, and warns about partners the register shows as dissolved.
verified: 19.0.2.0.1
---

## What it is for {#purpose}

A Slovak business has to state on its documents which register it is entered
in and under which number. Odoo's Slovak localization gives the company a
single free-text field, **Trade Registry**, for that sentence. It is typed once
and then forgotten — and goes on being printed after the court or the number
has changed.

This module:

- keeps the three coordinates — **Register**, **Registrový súd** (the
  authority keeping the entry), **Číslo zápisu** — as separate fields, on your
  company and on any contact;
- composes the statement from them, in correct Slovak, and keeps the company's
  **Trade Registry** in step;
- shows on each Slovak contact what the register says about it: legal form,
  status, predmety podnikania (scope of business), filed účtovné závierky and
  previous names and seats;
- warns on an invoice or bill when the partner is dissolved, deleted or
  suspended.

The data is typed by hand or filled from the register by
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk),
whose field mapping points at these fields automatically.

## Legal background {#legal}

[§ 3a ods. 1 Obchodného zákonníka](law:sk/1991/513#paragraf-3a.odsek-1)
requires every entrepreneur to state, on business letters and orders in written
or electronic form (*obchodné dokumenty*), the business name, seat or place of
business, the legal form of a legal entity and the identification number.
Entrepreneurs entered in the commercial register or another register of
entrepreneurs also state **the designation of the register that entered them
and the entry number**. By
[§ 3a ods. 2 and 3](law:sk/1991/513#paragraf-3a.odsek-2) the same applies to
written official correspondence and to the entrepreneur's website.

## Setting it up {#setup}

*Settings → Companies*, open your Slovak company. Above **Trade Registry** are
three new fields:

| Field | Example |
|---|---|
| Register | Obchodný register |
| Registrový súd | Mestský súd Bratislava III |
| Číslo zápisu | Sro/12345/B — oddiel and vložka as the register writes them |

From them the module composes the statement and writes it into **Trade
Registry**, which Odoo's Slovak localization prints on invoices:

> Zapísaná v Obchodnom registri Mestského súdu Bratislava III, oddiel: Sro,
> vložka č.: 12345/B

- The register name is put in the locative and the authority in the genitive
  (*Mestský súd* → *Mestského súdu*, *Okresný úrad* → *Okresného úradu*).
  Names the module does not know are written exactly as entered.
- *Zapísaná* for a company, *Zapísaný* for an individual (a sole trader).
- *oddiel / vložka č.* only for the Obchodný register. Any other register
  gets *číslo zápisu: …* with the number as written, e.g. *Zapísaný v
  Živnostenskom registri Okresného úradu Trnava, číslo zápisu: 250-12345*.

**Your own wording wins.** If you type something else into **Trade Registry**,
the module leaves it alone from then on. The composed statement is also shown,
editable, as **§ 3a statement** on the contact behind the company; an edit there
reaches **Trade Registry** too and sticks until a coordinate changes again.
Clearing all three coordinates clears the statement the module wrote.

## The register on a contact {#partner}

Tab **Register (SK)** on a contact in Slovakia (or with no country):

| Group | Fields |
|---|---|
| Zápis | Register, Registrový súd, Číslo zápisu, Právna forma, Dátum vzniku, § 3a statement |
| Stav | Stav v registri, Dátum zániku, Veľkostná kategória, Register checked (when the register was last read), Posledná závierka, Roky bez závierky |

Below them, filled from the register and read-only:

- **Predmety podnikania** — each with its validity and any suspension. A
  predmet podnikania is a legal authorisation for a kind of work, not the
  statistical NACE code. If one is suspended with no end date, the tab says
  so: the subject is active but may not do that work.
- **Účtovné závierky (RÚZ)** — period, type and the filing, approval and
  preparation dates. Metadata only; no figures.
- **Predchádzajúce názvy a sídla** — previous names and registered seats with
  their validity, useful for matching an old document to today's partner.

The button **Ask ORSF to re-read the registers** asks ORSF to fetch the subject
again from the source registers, for when its copy is incomplete. The fresh data
arrives about a minute later; then run *Actions → Update* on the contact. The
button needs the ORSF module.

## Dissolved partners {#dissolved}

When **Stav v registri** is *Zrušená*, *Vymazaná* or *Pozastavená*:

- a yellow banner at the top of the contact says the subject is not trading,
  with the date of dissolution if known, and the contact is greyed out in the
  contact list (the status column can be shown there);
- an invoice, credit note or receipt of a company whose fiscal country is
  Slovakia shows a warning naming the status, the date and when it was checked
  in the register. On a vendor bill it adds that the supplier may not have
  existed at the time of supply, so the right to deduct VAT should be checked;
- when such a document is posted, the warning is also written to its chatter.

The warning never blocks posting. A final invoice or a late bill from a wound-up
partner can be perfectly legitimate; the date on the document decides, and only
a person can judge that.

To see every such partner at once, open *Accounting → Customers → Zrušené
subjekty (SK)*, or use the filter **Zrušené subjekty (SK)** in any contact
list — customers, vendors or contacts.

## Limitations {#limitations}

- Odoo's Slovak localization prints **Trade Registry** on invoices only, with
  the label *Obchodný register:*. § 3a also covers orders, letters and the
  website; put the statement there yourself.
- The declension covers a short list: Obchodný / Živnostenský register, the
  registers of foundations, civic associations and non-profit organisations,
  and Mestský / Okresný / Krajský súd and Okresný úrad. Anything else is
  printed as entered, which may read stiffly. Check the sentence once.
- *Zapísaná* is right for a spoločnosť; for a družstvo or another neuter form,
  overwrite the statement.
- **Roky bez závierky** counts from the previous calendar year, whatever the
  filing deadline: early in the year a partner whose last závierka is for the year
  before last shows 1 although the deadline for the latest may not have passed.
- Everything except the coordinates comes from ORSF. Without it, the status,
  lists and warning stay empty unless you enter the status by hand.
