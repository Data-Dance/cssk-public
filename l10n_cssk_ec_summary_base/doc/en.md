---
title: CZ/SK EC Sales List
summary: The shared screens and workflow behind the Slovak súhrnný výkaz and the Czech souhrnné hlášení — one line per customer, VAT number and transaction code, checked and exported as XML.
verified: 19.0.1.7.1
---

## What it is for {#purpose}

A VAT payer that supplies goods or services to customers registered for VAT
in another EU member state reports those supplies on an **EC sales list**:
the Slovak *súhrnný výkaz* (SV) and the Czech *souhrnné hlášení* (SH). Both
have the same shape — one line per customer VAT number and transaction code,
carrying the total value supplied to that customer in the period.

This module provides that shape: the list itself, its computation from posted
journal items, the checks run before export and the XML export pipeline. It
does nothing on its own. The country module supplies the codes, the official
XML template and the schema:

- [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) — Slovak súhrnný výkaz;
- [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) — Czech souhrnné hlášení.

The legal background — who must file, how often and by when — is on those
pages. This page describes the screens both countries share.

## Setting it up {#setup}

1. **Intra-EU supply taxes carry a transaction code.** A journal item reaches
   the list only through a tax marked with an *EC sales list code* (technical
   field `cssk_ec_summary_code`). The country module sets the code on the
   standard intra-EU taxes of Odoo's Czech or Slovak chart of accounts when it
   is installed (see its page). On a tax you create yourself, or the taxes of
   a company whose chart is installed later, set **EC sales list code** on the
   tax form (*Advanced Options*, shown on Czech and Slovak sales taxes).
2. **The company's VAT number** (*Tax ID*) must be set; the export refuses
   without it.
3. **The tax office.** *Accounting → Configuration → Settings*, block
   **Czech / Slovak Localization**, setting **Default tax authority**. The XML
   names the office from it.
4. **Customers.** Every customer on an intra-EU invoice needs a VAT number with
   its country prefix and a country on its address. The line takes its country
   from the address, not from the VAT prefix.

## Preparing a list {#usage}

*Accounting → Reporting → Statutory Reports → EC Sales List*, then *New*.

1. Fill in the period (*Date From*, *Date To*), the **Period Type** (monthly or
   quarterly), the **Version** and the **Statement Type** (regular, corrective,
   supplementary — the names come from the country module). Only versions
   valid for the period are offered; see [Versions](#versions).
2. Click **Compute**. The list moves to *Preview* and shows one line per
   **country, customer VAT number and transaction code**, with the number of
   documents and the total value.

What is counted:

- posted journal items of the company that carry a coded tax;
- the value is the item's balance in company currency (CZK or EUR), with the
  sign turned so that a supply is positive and a credit note negative;
- the period follows the **taxable supply date** for customer invoices and
  credit notes (the accounting date when the document has none), and the
  accounting date for everything else. Where a document records a *VAT period
  declared* date, that date wins.

On each line:

| Column | Meaning |
|---|---|
| ✓ | The source items still add up to the line's value (within 0.50). |
| **Documents** | Opens the journal items behind the line, grouped by document. |
| **Override** / *Manual Value* | Tick to report a value of your own — for example a correction that is not yet booked. The line turns orange. |

**Compute** can be repeated while the list is in *Draft* or *Preview*. Manual
overrides survive it: they are re-applied to the line with the same country,
VAT number and code. An override whose line no longer exists is listed in the
chatter, never dropped silently.

## Exporting and filing {#submission}

Click **Export XML**. Before anything is generated, the export checks:

1. the company's VAT number;
2. the VAT number of every line — it must be present, start with two letters,
   and the line's country must be an EU member state. Any failure is a **hard
   block** listing the offending lines;
3. the country module's own rules (for example the allowed transaction codes);
4. the generated XML against the official schema of the version.

The XML is then attached to the list (*Xml Attachment*) and the state becomes
*Exported*. The list can be exported again while it is *Exported*.

Upload the file to the tax authority's portal, or file it through a channel
(below), then click **Mark Submitted**. The filed copy is frozen: it is kept
in *Filed history* even if the list is later reset and filed again, and a
submitted list cannot be deleted.

**File it** opens a delivery record for the exported or submitted list. With
only the standard channel it records that the filing was made by hand on the
portal and keeps the receipts. With
[module:l10n_cz_epo](module:l10n_cz_epo) installed, a Czech list can be signed
and sent to EPO directly. The badge in the header shows the delivery state.

**Reset to Draft** reopens an exported or submitted list. Only users in the
group *Accounting / Administrator* may do it; the filed copy is kept.

## Corrections {#corrections}

On a submitted list, **Dodatočný / opravný** creates a copy linked to the
original (*Amends*) and opens it in draft. Change its **Statement Type** to
the corrective or supplementary type, then compute and export as usual. The
copy starts with no lines and is recomputed from the current bookings.

A corrective list that replaces the original reports the **full list**. A
later filing that reports changes only — the Slovak *dodatočný* výkaz, the
Czech *následné* hlášení — is reduced on **Compute** to what changed against
the filings recorded for the period (submitted or historical, in filing
order): new rows as they are, changed rows corrected, rows that are gone
withdrawn. How a row is withdrawn is the country's: Slovakia files it with
value 0, the Czech form with a storno row, shown greyed out with *Cancels a
filed row* ticked. Such a filing with no recorded filing of its period is
refused. See the country pages.

A list imported from a previous system as a **historical filing** is a record
of what was filed: it cannot be recomputed, exported or submitted, but a
correction can be raised against it. A **Comparisons** button appears on a
list that has been compared with another basis, such as a fresh computation.

## VIES check with consultation numbers {#vies}

The check above is a format check only. With
[module:l10n_cssk_vies](module:l10n_cssk_vies) installed, the add-on
[module:l10n_cssk_ec_summary_vies](module:l10n_cssk_ec_summary_vies) installs
itself and makes the export ask the European Commission's VIES service about
every line — but only for companies that have **Use direct EU VIES (no IAP)**
switched on (*Accounting → Configuration → Settings*, under **Verify VAT Numbers**).

For each line it stores *VIES Valid*, *VIES Status*, the *VIES Consultation
No.* returned by VIES and *VIES Checked On* (hidden by default), so a filed
list shows what was confirmed and when.

- A VAT number VIES reports as **invalid** blocks the export. The list shows a
  sticky warning and the chatter names the lines; the consultation numbers
  obtained for the valid lines are kept, so the next attempt does not lose
  them.
- When VIES **cannot be reached**, the line is marked *Service fault* and the
  export goes ahead, so an outage does not make you miss the deadline. The
  chatter lists those lines; export again later to repeat the check.
- Every export queries VIES again, once per line.

## Versions {#versions}

*Accounting → Configuration → CZ/SK Localization → EC Sales List Versions*
lists the form versions the country modules install: validity dates, the XML
template, the schema and, on the *Submission Types* tab, the statement types
with the value each writes into the XML. A list offers only the versions
whose validity covers its period, including archived ones, so archiving a
version tidies the list without making old periods unfileable. You normally
do not change anything here.

**Export warnings.** Checks that do not stop the export are listed in a
yellow banner at the top of the form, and in the chatter, until the next
export.

## Limitations {#limitations}

- The transaction code is read only from the tax (see
  [Setting it up](#setup)).
- The line's country comes from the customer's address. The VAT-prefix codes
  that differ from the ISO country code — **EL** for Greece, **XI** for
  Northern Ireland — are not derived; a Northern Ireland customer with a
  United Kingdom address fails the EU check.
- The *Allow Monthly* / *Allow Quarterly* flags on a version refuse a period
  type the form does not have; whether you may file quarterly is for you to
  decide under the national rules.
- A correction is compared only with the filings recorded here (see
  [Corrections](#corrections)).
- Call-off stock (the *režim call-off stock* / *režim skladu*) is not
  supported by either country module.
- Without the VIES add-on, the check before export is a format check, not a
  validity check.
