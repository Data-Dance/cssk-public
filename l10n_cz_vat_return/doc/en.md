---
title: CZ VAT Return (DPHDP3)
summary: The Czech VAT return computed from the tax tags of Odoo's Czech chart and exported as the EPO DPHDP3 XML, validated against the current official XSD for every period.
verified: 19.0.1.11.0
---

## What it is for {#purpose}

The Czech layer of the [shared VAT-return engine](module:l10n_cssk_vat_return_base).
It supplies:

- the **DPHDP3** form (*přiznání k dani z přidané hodnoty*): its rows mapped
  to the tax tags of Odoo's Czech chart (`l10n_cz`), the EPO XML template
  (`Pisemnost / DPHDP3`) and the official schema;
- the filer block of the XML from the company's EPO data;
- bad-debt corrections reported on ř. 33 and ř. 34;
- repairs to the Czech chart's taxes without which several rows would stay
  empty or wrong;
- the archived rates in force before today's, for importing older documents.

How to create, compute, review, export and file a return is described on the
[engine's page](module:l10n_cssk_vat_return_base#usage); this page covers what
is Czech.

## Legal background {#legal}

- **Who files.** Every VAT payer (*plátce*) and identified person files a
  return — [§ 101 odst. 1 of the VAT Act](law:cz/2004/235) — and a payer files
  one even for a period in which no tax arose
  ([§ 101 odst. 3](law:cz/2004/235)).
- **Tax period.** The calendar month ([§ 99](law:cz/2004/235)). A payer may
  choose the calendar quarter for a year if its domestic turnover for the
  preceding year did not exceed CZK 15 000 000, it is not an unreliable payer
  or a VAT group, and it notifies the tax office by the end of January
  ([§ 99a odst. 1](law:cz/2004/235)).
- **Deadline.** For a tax period shorter than a year the return is filed
  within **25 days after the end of the period**, and the deadline cannot be
  extended — [§ 136 odst. 4 of the Tax Procedure Code](law:cz/2009/280).
- **Electronic filing in the prescribed structure.** A payer must file the
  return and any supplementary return electronically
  ([§ 101a odst. 1](law:cz/2004/235)); a filing not made in the prescribed
  format or structure is ineffective ([§ 101a odst. 4](law:cz/2004/235)).
- **Corrective and supplementary returns.** Before the deadline a return may be
  replaced by an *opravné daňové přiznání*
  ([§ 138 of the Tax Procedure Code](law:cz/2009/280)). After it, a payer that
  finds the tax should be higher than the last known tax files a *dodatečné
  daňové přiznání* by the end of the month following the month of discovery
  ([§ 141 odst. 1](law:cz/2009/280)), stating the difference against the last
  known tax and the day it was found ([§ 141 odst. 5](law:cz/2009/280)).
- **Bad debts.** The creditor's correction of the tax base for an
  unrecoverable receivable is governed by [§ 46 and following of the VAT
  Act](law:cz/2004/235), the debtor's matching reduction of its deduction by
  [§ 74b](law:cz/2004/235).

## The form and its structure {#form}

The Czech Financial Administration publishes **one** DPHDP3 schema,
`dphdp3_epo2.xsd`, and replaces it in place; every return — for the current
period or an old one — is filed in the structure current at the time of
filing. The module therefore ships a single, open-ended version,
**DPHDP3 (aktuální struktura)**, with that schema and the XML declared as
`verzePis="03.01.04"` — structure 03.01.04 of 11. 8. 2026. Because nothing in
the schema says which revision it is, the module pins the file's checksum and
the structure version in `data/SCHEMA_VERSION`, with the procedure for
refreshing them; a test fails if the bundled file or the template's
`verzePis` drifts from the pin. It is offered for periods from
**1 January 2016**; that
start date is a conservative bound chosen by the module, not a statutory one,
and there is no version for earlier periods.

Amounts are exported in whole crowns. The filing date in the XML
(*d_poddp*) is the day of the export.

## Setting it up {#setup}

Beyond the [engine's setup](module:l10n_cssk_vat_return_base#setup), the XML
needs, on the company:

| Where | What |
|---|---|
| *Tax ID* | The DIČ (written without `CZ`). |
| *Finanční úřad* | The tax office; its submission code goes into *c_ufo*. |
| *Finanční Úřad (CZ)* | The territorial office (*územní pracoviště*), *c_pracufo*. |
| *Typ osoby / subjektu* | Decides whether the filer is a natural person or a legal entity. |
| tab **EPO podání** | For a legal entity the *oprávněná osoba* (name and position), for a natural person the name and title; *Sestavil* (who prepared the return) and, if any, *Zástupce*. |
| *NACE (main activity)* | The main CZ-NACE activity code, *c_okec*; EPO reports a return without it as a serious error. |
| address, phone, e-mail | The filer's address (street and number are split), *c_telef*, *email*. |

The payer type (*typ_platce*) is always **P** (payer) unless
[module:l10n_cz_vat_status](module:l10n_cz_vat_status) records another status.

## The Czech return {#usage}

The statement types are **Řádné** (B), **Opravné** (O), **Dodatečné** (D) and
**Dodatečné/opravné** (E). Each row's code is the attribute name in the XML
(`obrat23`, `dan23`, `odp_tuz23_nar` …) and its name gives the form's row
number, e.g. *R1 tax_base*.

**Computed from tags**: rows 1–13 (base and tax), 20–26, 30, 32, 33, 34, the
base and the full deduction of rows 40–44 and 47, row 50, 51 and 61.

**Computed from the other rows**, as the EPO structure defines them, after
the rows above (each summed in whole crowns, as exported, so the totals foot):

| Row | Formula |
|---|---|
| 46 | sum of rows 40–45, in each column (*v plné výši*, *krácený odpočet*) |
| 62 | rows 1–13 (tax) − row 61 |
| 63 | row 46 *v plné výši* + row 52 + row 53 + row 60 |
| 64 | row 62 − row 63 when positive (vlastní daň) |
| 65 | row 63 − row 62 when positive (nadměrný odpočet) |
| 66 | row 62 − row 63, on a dodatečné return only |

An **Override** on any of them is kept and feeds the rows after it. Rows 64
and 65 are left out of the XML of a dodatečné return, and row 66 out of any
other. The tax under § 108 odst. 4 písm. g) and h), which the form adds to
row 62 but has no row of its own, is not modelled: add it to row 62 with
**Override** where it arises.

Rows 64 and 65 also drive the return's *Settlement* tab (amount to pay or
refund, and the carry of an excess deduction).

**Manual** — enter them with **Override**, or they are exported as 0:

| Row | Content |
|---|---|
| 31 | triangular trade, middle person |
| 40–44, 47 (*reduced_claim*) | the deduction in reduced amount (*v krácené výši*) |
| 45 | correction of deduction |
| 52, 53 | coefficients and the settlement of the deduction |
| 60 | adjustment of deduction |

**Content checks at export**: rows 64 and 65 must not be negative and must
not both be filled.

**A dodatečné return** (types D and E) cannot be exported without **Důvody
zjištěny dne** (*d_zjist*), shown next to the statement type. It is the same
date as the engine's *Den zjištění rozdílu* (one field, shown once under its
Czech name), so an amendment created with the button already carries it.

**Filing through EPO.** With [module:l10n_cz_epo](module:l10n_cz_epo)
installed, **File it** offers the EPO channel: the return can be checked in
EPO's test mode and filed with the company's certificate.

## Repairs to the Czech chart {#chart-fixes}

On install and whenever a company loads the Czech chart, the module adjusts
the chart's taxes so that the return can report them:

- **Deduction of self-assessed tax (ř. 43 and 44).** `l10n_cz` tags only the
  declaration of a reverse charge or an EU acquisition, so the deduction
  reached no row. The deduction legs get new tags *VAT 43 Base/Total* and
  *VAT 44 Base/Total*, the band taken from the row the tax declares on.
- **Import of goods (ř. 7 and 8).** Those taxes had a single tax leg, so a
  bill from a non-EU supplier asked you to pay the supplier the Czech VAT on
  top of the invoice; a cancelling deduction leg is added. Row 9 (new means of
  transport) is left as it is.
- **Credit notes on EU reverse charges.** Four taxes named the tax account on
  the invoice side only; the refund side gets the same account, so a
  reverse-charge credit note no longer leaves its VAT on the expense account.
- **Intra-Community purchases.** Under the *Intra-Community* fiscal position
  the domestic purchase taxes (21 % and 12 %, goods and services) are mapped to
  the EU acquisition taxes, so a bill from an EU supplier self-assesses the tax
  instead of keeping the Czech rate. Only links are added; a mapping set by
  hand is kept.

## Bad-debt corrections {#bad-debt}

A document flagged with **Oprava u nedobytné pohledávky** (a field added by
`l10n_cz_statutory`) leaves every ordinary row of the return. Its tax goes to
**ř. 33** when it is a sales document (the creditor's correction) or **ř. 34**
when it is a purchase document (the debtor's), in addition to any entry tagged
*VAT 33* / *VAT 34* by hand.

## Historical rates {#historic-rates}

On install and whenever a company loads the Czech chart, the rates no longer
in force are created as archived taxes (see the
[engine's page](module:l10n_cssk_vat_return_base#historic-rates)). Each is
cloned from today's rate of the same band, because DPHDP3 keeps the standard
rate (rows 1/2, deduction row 40) apart from the reduced one (rows 3/4, row 41):

| Rate | In force | Cloned from |
|---|---|---|
| 19 % | 1. 5. 2004 – 31. 12. 2009 | 21 % |
| 20 % | 1. 1. 2010 – 31. 12. 2012 | 21 % |
| 5 % | 1. 5. 2004 – 31. 12. 2007 | 12 % |
| 9 % | 1. 1. 2008 – 31. 12. 2009 | 12 % |
| 10 % | 1. 1. 2010 – 31. 12. 2023 | 12 % |
| 14 % | 1. 1. 2012 – 31. 12. 2012 | 12 % |
| 15 % | 1. 1. 2013 – 31. 12. 2023 | 12 % |

10 % is one tax for both of its periods (2010–2011 and 2015–2023), so the
three years between are not excluded by its dates.

## Limitations {#limitations}

- The reduced-amount deductions, rows 31, 45, 52, 53 and 60, are manual (see
  [above](#usage)), and so is the § 108 odst. 4 g)/h) part of row 62.
- The content checks cover rows 64 and 65 only; the schema cannot tell
  whether the other figures are consistent.
- Periods before 2016 have no version.
- On a dodatečné return the rows are the period's figures as recomputed, and
  row 66 is row 62 − row 63 of this return; it is not compared with the
  return being amended.
- The pin in `data/SCHEMA_VERSION` shows that the bundled schema is the one
  verified on a stated date, not that it is still current; refresh it by the
  procedure in that file.
- The rows follow `l10n_cz`'s tags. A tax created by hand without the right
  tags reaches the wrong row or none.
