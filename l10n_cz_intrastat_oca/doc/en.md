---
title: Czech Intrastat (InstatOnline CSV) — Community
summary: The monthly Czech Intrastat declaration generated on the OCA Intrastat engine as the CSV file the customs administration's InstatOnline portal imports.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A Czech business whose trade in goods with other EU countries reaches the
reporting threshold files a monthly **výkaz pro Intrastat** (Intrastat
declaration) with the customs administration (*Celní správa*): one for goods
dispatched to other EU countries and one for goods received from them.

On Community, the OCA module `intrastat_product` collects the figures from
invoices, but it has no Czech output. This module adds it: for a Czech
company, the declaration file is the **CSV** that the customs administration's
**InstatOnline** portal imports, instead of an XML file. The column layout,
the fixed values and the number format are those of Odoo Enterprise's own
Czech Intrastat module, so a company moving between editions files the same
data.

It is deliberately not named `l10n_cz_intrastat`: that is Odoo Enterprise's
module, which an Enterprise database uses instead. Install one or the other.

## Legal background {#legal}

- **EU framework.** Intrastat is part of the European business statistics of
  [Regulation (EU) 2019/2152](law:eu/reg/2019/2152). Article 13(1) lists what
  the exporting country passes on about each intra-EU export, including the
  **partner's VAT identification number** in the country of import and the
  **country of origin**.
- **Who reports, and when** — [celní zákon (Customs Act) No. 242/2016 Sb.,
  § 57 to § 60](law:cz/2016/242):
  - a reporting unit (*zpravodajská jednotka*) reports once it reaches the
    threshold (§ 57 odst. 1), for calendar months (§ 58 odst. 2), until the
    end of that year and for the whole following year (§ 58 odst. 4);
  - the declaration is due **no later than the 12th working day** of the
    following month, filed through the electronic portal run by the
    General Directorate of Customs (§ 58 odst. 5);
  - corrected or missing data must be reported **within 30 days** of
    learning of the error (§ 60 písm. a).
- **Thresholds** — [nařízení vlády (government decree) No. 333/2021 Sb.,
  příloha č. 3](law:cz/2021/333): the reporting threshold is
  **15 000 000 Kč** of goods dispatched, and separately 15 000 000 Kč of goods
  received, counted from the beginning of the calendar year; each flow is
  declared separately from the month in which it reached the threshold.

The module does not check thresholds. Set the flows in the settings according
to your obligation.

## Setting it up {#setup}

1. *Accounting → Configuration → Settings*, block **Intrastat**: set
   **Arrivals** (*Přijetí*) and **Dispatches** (*Odeslání*) to *Standard* or
   *Extended* for each flow you report, *Exempt* for the other; optionally a
   **Default Transport Mode**.
2. Commodity codes must exist in Odoo: enter them, or load the Combined
   Nomenclature with the OCA module `intrastat_product_hscodes_import`, which
   this module does not install by itself.
3. On each stockable product: **Kód zboží (KN)** (*H.S. Code*), **Země
   původu** (*Country of Origin*) and the **weight** in kg.
4. Your company needs its **DIČ** (VAT number); without it the file is not
   generated.

## Monthly declaration {#usage}

*Accounting → Reporting → Intrastat → Výkaz produktů Intrastat*
(*Intrastat Product Declaration*), then *New*. On Community without full
accounting the menu root reads *Fakturace*.

1. Choose the **year**, **month** and **type** — *Přijetí* (Arrivals) or
   *Odeslání* (Dispatches).
2. **Generovat řádky z faktur** (*Generate Lines from Invoices*), check the
   **Transakce** tab, correct invoices or products and regenerate as needed.
3. **Potvrdit** (*Confirm*) groups the transactions into declaration lines.
4. **Generovat XML soubor** (*Generate XML File* — the button keeps the
   engine's name) creates the CSV, attaches it as
   `YYYY-MM_<type>_<revision>.csv` and marks the declaration *Dokončeno*.
5. Upload the file in **InstatOnline** on the customs administration's
   portal, which checks it on upload (there is no schema to validate against
   in advance).

Each line of the file holds: month; year; your DIČ; flow (`A` arrivals,
`D` dispatches); partner's VAT number; partner country; region (empty);
country of origin; nature of transaction (two digits, e.g. `11`); mode of
transport; delivery terms (Incoterm); code of movement `ST`; commodity code
(spaces removed); statistical sign and description (both empty); net mass;
quantity in supplementary units; invoiced value in the company currency.
Mass and supplementary units up to 1 are written with three decimals, larger
ones as whole numbers.

## Statutory footprint {#footprint}

With [module:l10n_cssk_core](module:l10n_cssk_core) installed,
[module:l10n_cssk_intrastat_footprint](module:l10n_cssk_intrastat_footprint)
installs itself and lists, in the **Statutory footprint** of a posted
document, every Intrastat declaration that took one of its lines — period,
flow and state — with a link. A month whose declaration has not been
generated yet shows nothing. The full description is in
[the Slovak Intrastat guide](module:l10n_sk_intrastat#footprint).

## The shared renderer {#engine}

The CSV itself is produced by
[module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base), which also
renders the Slovak INSTAT XML. It has no screens and installs automatically
with this module.

## Limitations {#limitations}

- **Decimals are cut off, not rounded**: net mass and supplementary units
  above 1, and the invoiced value, are written as their whole-number part
  (13.9 kg becomes 13; 800.75 Kč becomes 800). This matches Odoo
  Enterprise's Czech module; check it against InstatOnline's rules if your
  values carry decimals.
- Region, statistical sign and description of goods are always left empty;
  the code of movement is always `ST`.
- Corrections: a copied declaration gets the next revision and a new file
  name, but the file itself has no correction marker. Make corrections in
  InstatOnline within the 30-day limit.
- The simplified declaration (*zjednodušené hlášení*) is not produced.
- Thresholds are not checked: the module files what you ask it to file.
- Filing happens in InstatOnline, outside Odoo.
