---
title: CZ EC Sales List (Souhrnné hlášení)
summary: The Czech EC sales list — souhrnné hlášení, EPO form DPHSHV — computed from the intra-EU supply taxes of Odoo's Czech chart and exported as EPO XML.
verified: 19.0.1.3.0
---

## What it is for {#purpose}

A Czech VAT payer that supplies goods or services to customers registered for
VAT in another EU member state reports them on the **souhrnné hlášení**
(*EC sales list*), filed electronically through the Financial Administration's
EPO as the form **DPHSHV**.

This module is the Czech layer of
[module:l10n_cssk_ec_summary_base](module:l10n_cssk_ec_summary_base), which
holds the screens and the workflow — preparing the list, reviewing lines,
exporting and filing are described [there](module:l10n_cssk_ec_summary_base#usage).
This module adds the Czech transaction codes, the DPHSHV XML template and the
official schema, and codes the standard taxes of Odoo's Czech chart.

## Legal background {#legal}

All references are to [§ 102 of the VAT Act, No. 235/2004 Sb.](law:cz/2004/235)
(*zákon o dani z přidané hodnoty*). Statutory terms are given in Czech.

- **Who files.** A payer (*plátce*) that must declare an intra-EU supply of
  goods to a person registered for VAT in another member state, a transfer of
  its own goods to another member state, a supply to the buyer in a triangular
  trade where it is the middle party, or a service with its place of supply in
  another member state under § 9 odst. 1 for which the recipient accounts for
  the tax (§ 102 odst. 1). Also a payer moving goods under the call-off-stock
  regime (*režim skladu*, odst. 2), and an identified person (*identifikovaná
  osoba*) for such services and triangular supplies (odst. 3).
- **Period and deadline.** A payer files **for each calendar month within
  25 days** after its end (odst. 5). A payer whose only reportable supplies are
  services files **within the deadline for its VAT return** (odst. 6) — so a
  quarterly VAT payer files quarterly — until it makes a supply of goods; from
  then on it files monthly to the end of that calendar year (odst. 7).
- **Currency.** Values are stated in Czech crowns (odst. 4).
- **Corrections.** On finding an error in a filed list, the payer must file a
  **následné souhrnné hlášení** within **15 days** of discovering it (odst. 8).

The transaction codes (*kód plnění*) are those of the EPO form instructions,
as carried in the official schema:

| Code | Supply |
|---|---|
| 0 | supply of goods to a person registered for VAT in another member state (§ 13 odst. 1 and 2) |
| 1 | transfer of the payer's business assets to another member state (§ 13 odst. 6) |
| 2 | supply in a triangular trade (§ 17), filled in only by the middle party |
| 3 | service with its place of supply in another member state (§ 9 odst. 1) |

## Form version {#version}

The module installs **one** version, *Souhrnné hlášení 2025*, valid from
1 January 2010 with no end date. It renders the EPO structure *Pisemnost /
DPHSHV* (`verzePis` 02.01.05, the structure of 11. 8. 2026) and validates it
against the bundled schema `dphshv_epo2.xsd`. The schema's checksum and the
structure version are pinned in `data/SCHEMA_VERSION`, with the procedure for
refreshing them, and a test fails when the file or the template's `verzePis`
drifts from the pin.

One open-ended version is deliberate: the Czech Financial Administration
publishes a single schema per form and updates it in place, and EPO takes
every period in the current structure. There is no older Czech form to choose
by year; the "2025" in the name is only a label.

The XML contains the header (*VetaD*: year, month or quarter, the form type),
the filer block (*VetaP*, taken from
[module:l10n_cz_statutory](module:l10n_cz_statutory) without e-mail and
telephone, which the form does not have) and one *VetaR* per line: country
code, the customer's VAT number without the country prefix, the code, the
number of supplies and the total value in whole crowns. A storno row carries
`k_storno="A"` with the country, VAT number and code only.

## Setting it up {#setup}

When the module is installed, it sets the transaction code on the intra-EU
taxes of every company that uses the Czech chart of accounts at that moment,
unless a code is already there:

| Tax of Odoo's Czech chart | Code |
|---|---|
| 0% EU G — intra-Community supply of goods | 0 |
| 0% EU S — intra-Community supply of services | 3 |

There is no standard tax for codes **1** and **2**. If you transfer your own
goods or act as the middle party in a triangular trade, the tax you use for it
has to be coded yourself — see
[setting up the framework](module:l10n_cssk_ec_summary_base#setup), which also
lists the company data the export needs (VAT number, the tax office under
*Default tax authority*).

## Preparing and filing {#usage}

Follow the [shared workflow](module:l10n_cssk_ec_summary_base#usage) at
*Accounting → Reporting → Statutory Reports → EC Sales List*. The statement types
this module offers are *Řádné*, exported as form **R**, and *Opravné* and
*Následné (dodatečné)*, both exported as **N** (následné souhrnné hlášení):
the form knows only these two, and § 102 has no opravné hlášení.

**A následné hlášení reports only the changes.** On **Compute** the module
compares the recomputed period with what was filed for it — the statements of
the same period marked submitted, or recorded as historical filings, taken in
the order they were filed — and keeps:

- a row that is **new**, as it is;
- a row whose value (in whole crowns, as exported) **changed**, as a storno
  row cancelling the filed one followed by the corrected row;
- a row filed earlier that is **gone**, as a storno row only.

Unchanged rows are left out. Storno rows are shown greyed out with *Cancels
a filed row* ticked. A následné hlášení with no filed statement of its period
recorded here is refused: mark the original submitted, or import it as a
historical filing, first.

The export writes the country code of each customer's VAT number as the form
lists it — **EL** for Greece, **XI** for Northern Ireland — and rounds each
value **up** to whole crowns. A customer with an XI number is accepted for
goods only; a service to one stops the export.

After **Export XML**, upload the file to EPO, or use **File it**: with
[module:l10n_cz_epo](module:l10n_cz_epo) installed the list can be sent to
EPO in test mode or filed directly, signed with the company's certificate.

## Limitations {#limitations}

Check the following before you rely on the export for a live filing:

- **Corrections are compared with what is recorded here.** A filing made
  outside Odoo and not recorded as a historical filing is invisible to the
  comparison.
- **Codes are not checked.** Any single digit passes the export; only codes
  0–3 exist.
- The call-off-stock register (*režim skladu*, § 102 odst. 2) is not
  supported.
- Choosing monthly or quarterly filing, and switching to monthly after a
  first supply of goods (odst. 7), is up to you; the module does not check it.
