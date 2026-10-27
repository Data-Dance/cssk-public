---
title: CZ/SK OSS VAT Return (Union scheme)
summary: The quarterly One-Stop-Shop VAT return for distance sales and services to consumers in other EU states — computed from Odoo's OSS taxes, converted to euro at the ECB rate, with corrections of earlier quarters.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

A seller registered for the **One-Stop-Shop, Union scheme** charges the VAT of
the customer's member state on distance sales of goods and on services to
consumers in other EU states, and declares all of it in one quarterly return
filed at home: in Czechia the *daňové přiznání ve zvláštním režimu jednoho
správního místa — režim Evropské unie*, in Slovakia the *daňové priznanie k DPH
— osobitná úprava pre Úniu*.

Odoo's own module `l10n_eu_oss` already creates what is needed to *charge* that
VAT: one *OSS B2C* fiscal position per member state and destination-rate sale
taxes, all tagged `OSS`. What Odoo does not produce for Czechia or Slovakia is
the *return*. This module computes it from those tagged journal items:

- one row per **member state of consumption × goods/services × VAT rate**,
  in euro;
- **corrections of earlier quarters** per member state;
- the balance per member state and the total VAT due.

The statutory XML comes from a national module, which you install alongside:

| Member state of identification | Module | Form |
|---|---|---|
| Czechia | [module:l10n_cz_oss](module:l10n_cz_oss) | EPO form OSSEI1 |
| Slovakia | [module:l10n_sk_oss](module:l10n_sk_oss) | eForm DPOSS_EUv01 |

The module also fills a gap in Odoo's OSS tax mapping for the Slovak 5 % rate —
see [The Slovak 5 % rate](#tax-mapping). It works on Community and Enterprise
alike: Enterprise's own OSS report exports only Belgium and Luxembourg.

## Legal background {#legal}

Both member states implement the same EU rules, and the module follows them
where they agree:

- **A quarterly return, due at the end of the following month**, filed even
  when nothing was supplied — CZ
  [§ 110zb and § 110zc of the VAT Act](law:cz/2004/235); SK
  [§ 68b ods. 12](law:sk/2004/222#paragraf-68b.odsek-12). In both acts the
  deadline does not move when it falls on a weekend or holiday.
- **Amounts in euro.** Amounts invoiced in another currency are converted at
  the European Central Bank rate for the last day of the quarter, or for the
  next day of publication if none was published for that day — CZ
  [§ 110ze odst. 2 písm. a)](law:cz/2004/235); SK
  [§ 68b ods. 17](law:sk/2004/222#paragraf-68b.odsek-17) (which also allows
  the rate declared by Národná banka Slovenska).
- **Corrections go into a later return**, naming the member state, the
  quarter and the amount of tax, within **three years** of the deadline of the
  original return, at the rate the original supply used — CZ
  [§ 110zd and § 110ze odst. 2 písm. b)](law:cz/2004/235); SK
  [§ 68b ods. 19](law:sk/2004/222#paragraf-68b.odsek-19).

The national guides cover registration, filing and the forms themselves.

## Setting it up {#setup}

1. **Odoo's OSS mapping.** *Accounting → Configuration → Settings*, block
   **EU Intra-community Distance Selling**, button **OSS Tax mapping**. This
   creates the OSS fiscal positions and taxes. Check them against what you
   actually sell, as Odoo itself asks.
2. **Product types.** Each row is split into goods and services from the
   product on the invoice line: a product of type *Service* is a service,
   everything else — including a line with no product — counts as goods.
   Sellers of electronic or other services should put products on their lines.
3. **Exchange rates.** If you invoice in currencies other than euro, keep the
   company's rates up to date: the return proposes its rates from that table.
4. **The form version.** The national module installs it. It is listed under
   *Accounting → Configuration → CZ/SK Localization → OSS Return Versions*,
   with its form code, validity, template and the official XSD; there is
   normally nothing to change there.

## Preparing the return {#usage}

*Accounting → Reporting → Statutory Reports → OSS VAT Return*, then *New*.

1. **Year** and **Quarter**, and the form version for your country (the field
   lists only versions of the company's member state valid for that quarter).
   The return can be made from the third quarter of 2021, when the Union
   scheme began.
2. **Registered from / Registered until** only if the registration began or
   ended during the quarter. The dates are written into the form as the start
   or end of the period, and only documents dated within them are taken. Both
   must fall within the quarter.
3. Click **Compute**. The module takes every posted journal item carrying the
   `OSS` tag:
   - an invoice belongs to the quarter of its taxable supply date, or of its
     invoice date when that is empty;
   - a credit note belongs to the quarter in which it was **issued** — the
     quarter in which the change became known;
   - the member state comes from the OSS tax (each OSS tax belongs to one
     destination), falling back to the document's fiscal position and then to
     the delivery address.
4. Check the three tabs:
   - **Supplies** — the rows, with taxable amount and VAT in euro. VAT on a row
     is computed as taxable amount × rate. The magnifier opens the journal
     items behind a row.
   - **Corrections of earlier quarters** — see [Corrections](#corrections).
   - **Exchange rates** — see [Exchange rates](#rates).
5. *VAT booked (EUR)* shows the OSS VAT actually posted on the documents,
   converted the same way, next to the computed totals. Compare the two.

Rows and corrections can be added or edited by hand while the return is a
draft. A row you add is *Manual* already; tick *Manual* also on a computed
row you change. **Compute** keeps manual rows and replaces all others, so an
edit to an unticked computed row is lost on the next run. On a manual row you enter both the taxable amount and
the VAT.

Supplies of goods dispatched from a warehouse in another member state, or of
services from an establishment there, are reported separately for that state.
Nothing on a standard Odoo invoice says where goods were dispatched from, so
such rows are **not** computed: enter them by hand, with *Supplied from* and,
where you have one, *VAT no. there*.

## Corrections of earlier quarters {#corrections}

A credit note (or debit note) that names its original invoice, where that
invoice lies in an earlier quarter, does not reduce this quarter's rows. It
becomes a correction of the original quarter for that member state, converted
at the original quarter's rate. A credit note for an invoice of the same
quarter simply nets against the row.

A credit note that names no original invoice stays in this quarter. If it
makes a row negative, the export refuses the return — neither form accepts a
negative row. Link the credit note to its invoice, or enter the correction
by hand.

Before export the module checks that every correction concerns a quarter from
Q3 2021 up to the one before this return, and refuses a correction whose
three-year period has run out — that correction has to be made with the member
state of consumption directly.

## Exchange rates {#rates}

Amounts invoiced in euro are taken as invoiced. For every other currency the
return needs one rate per currency and reference date: the last day of this
quarter, and the last day of each quarter that a correction concerns.

**Compute** proposes each rate from the company's rate table, taking the first
rate dated on or after the reference date — the "next day of publication" rule.
The table may hold Czech National Bank or bank rates rather than ECB rates, and
nothing in it says which, so a proposed rate is marked *Company rate table (to
confirm)* and shown in red. Check each rate against the ECB reference rate,
correct it if needed (the rate is *units of the currency per 1 EUR*), and click
**Confirm ECB rates**. The export refuses a return with a missing or unconfirmed
rate. A rate you have confirmed or typed is kept on the next **Compute**.

## Export and filing {#export}

**Export XML** runs, in order:

1. the master data check — the company needs a VAT number in the form the
   national module expects;
2. the content checks: missing or unconfirmed rates, negative rows, a member
   state outside the EU, a supply to the state it is made from, a row whose
   rate type (standard or reduced) cannot be determined, and corrections out
   of period or out of time;
3. rendering the national form and validating it against the official XSD
   stored on the form version.

Any error stops the export with the reason. A valid file is attached to the
return, which moves to *Exported*.

File the XML as the national guide describes, then click **Mark Submitted**.
This keeps the filed XML as the filed copy and locks the return. **File it**
opens a submission record that tracks delivery and holds the receipts (see
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base)).
**Reset to Draft**, for accounting administrators only, reopens a submitted
return and keeps the copy that was filed.

The rate type of each row is read from a table of each member state's standard
rate and the date it took effect: a rate equal to the standard rate on the
last day of the quarter is *standard*, any other rate *reduced*.

## The Slovak 5 % rate {#tax-mapping}

Odoo's OSS tax map has no Slovak 5 % rate in either direction, although
[§ 27 ods. 3](law:sk/2004/222#paragraf-27.odsek-3) has applied it since
1 January 2025 to part of what was taxed at 10 % until 2024. Without a mapping
an OSS sale on that tax would keep the domestic rate. This module adds the
missing entries whenever Odoo's mapping runs, without changing Odoo itself:

- **Slovak 5 % → another member state**: the foreign rate Odoo already uses for
  the old Slovak 10 %.
- **Another member state → Slovak 5 %**, for a seller elsewhere selling to
  Slovakia: that state's lowest reduced rate, and also the Czech 12 % rate.

Odoo 19 links a domestic tax to an OSS tax only when it creates that OSS tax,
so a second domestic tax with the same destination rate — Slovak 5 % next to
19 %, for instance — would stay unmapped. The module links every such domestic
tax to the existing OSS tax. It only adds links; it never creates taxes or
changes a mapping already on a fiscal position.

On installation the mapping is completed for every company that already has
OSS taxes. Companies that never used OSS are left alone. These mappings are
proposals, like Odoo's own: check them against the goods you sell.

## Limitations {#limitations}

- Only the **Union scheme**. The non-Union and import (IOSS) schemes are not
  covered — Odoo has no taxes for them.
- Supplies dispatched from another member state, or made from an establishment
  there, are not detected; enter them as manual rows.
- Goods and services are told apart by product type only; a line without a
  product counts as goods.
- The comparison of *VAT booked* with the computed VAT, and the warning that a
  correction must be filed early to stay within three years, are only written
  to the server log; the form does not show them. Compare *VAT booked* with
  *VAT on supplies* plus *Corrections* yourself.
- VAT on a row is rounded to cents from the row's taxable amount, not summed
  from the invoices. The Czech act asks for two decimals *without rounding* —
  see the [Czech guide](module:l10n_cz_oss#limitations).
- Proposed exchange rates come from the company's rate table and must be
  checked by a person.
- The rate-type table and the 5 % mapping reflect rates known when the module
  was released. A later change of a standard rate needs a module update.
