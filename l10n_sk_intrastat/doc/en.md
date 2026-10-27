---
title: Slovak Intrastat (INTRASTAT-SK)
summary: The monthly INTRASTAT-SK declaration of goods moved to and from other EU countries, generated from your invoices as the INSTAT XML file the Finančná správa portal imports — in Community on the OCA engine, in Enterprise on Odoo's own Intrastat report.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

A Slovak business whose trade in goods with other EU countries exceeds the
statistical threshold reports it every month on the **INTRASTAT-SK**
declaration (*hlásenie INTRASTAT-SK*): one declaration for goods coming in
from other EU countries and one for goods going out. Each item states the
commodity code, partner country, country of origin, nature of transaction,
net mass, supplementary units, invoiced value, mode of transport and delivery
terms.

Odoo can collect these figures from invoices, but neither edition files a
Slovak declaration: Community has no Intrastat at all, and Odoo Enterprise's
Intrastat report has declarations for other countries but not for Slovakia.
This family closes that gap. It renders the official **INSTAT XML** message
(schema `instat62.xsd`), validates it against the schema before you get the
file, and you import that file on the INTRASTAT-SK portal.

There are two ways in, one per edition, and both produce the same file from
the same ledger:

| Edition | Module | Engine that collects the figures |
|---|---|---|
| Community | this module | OCA `intrastat_product` (declarations under *Accounting → Reporting → Intrastat*) |
| Enterprise | [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee) | Odoo's *Intrastat (Goods)* report and tax returns — see [Enterprise](#enterprise) |

Both call the same renderer, [module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base)
(see [The shared renderer](#engine)).

## Legal background {#legal}

- **EU framework.** Intrastat is part of the European business statistics of
  [Regulation (EU) 2019/2152](law:eu/reg/2019/2152). Its Article 13(1) lists
  what the exporting country passes on about each intra-EU export, including
  the **VAT identification number of the partner** in the country of import
  and the **country of origin**. That is why a dispatch item carries the
  customer's VAT number and every item carries the origin.
- **Who reports, and from when.** The Statistical Office of the Slovak
  Republic (*Štatistický úrad SR*) sets the reporting obligation; declarations
  are filed through the Finančná správa portal
  `intrastat.financnasprava.sk`. Per the Statistical Office's handbook for
  2026 (*Príručka pre spravodajské jednotky, vydanie 2026*):
  - the **threshold** (*prah oslobodenia*) for 2026 is **1 000 000 EUR** per
    flow, tracked separately for imports and exports within the EU;
    businesses whose main activity is in SK NACE 01–03 or 10–12 keep lower
    thresholds of 200 000 EUR (imports) and 400 000 EUR (exports);
  - the obligation for 2026 follows from the trade between 1 October 2024
    and 30 September 2025, or starts in the month the cumulative trade of
    2026 exceeds the threshold;
  - the declaration is due **by the 15th calendar day** after the month,
    moved to the next working day when that falls on a weekend or holiday;
  - a quarterly VAT payer still reports **monthly**.
- **Terminology.** Since the modernised system, the Statistical Office speaks
  of *dovoz tovaru v rámci EÚ* and *vývoz tovaru v rámci EÚ* where the older
  terms were *prijatie* and *odoslanie*. The OCA screens still say
  *Arrivals* / *Dispatches* (in Slovak *Prijatie* / *Odoslanie*); they are
  the same two flows.

The module does not decide whether you are obliged to report — it has no
threshold logic. Set the flows in the settings according to your obligation.

## Setting it up (Community) {#setup}

1. *Accounting → Configuration → Settings*, block **Intrastat**: set
   **Arrivals** and **Dispatches** to *Standard* or *Extended* for each flow
   you report, *Exempt* for one you do not. Optionally set a **Default
   Transport Mode**.
2. Load the commodity codes once: *Accounting → Configuration → Intrastat →
   Load Intrastat Codes* (an OCA wizard installed with this module, also
   offered right after installation) imports the Combined Nomenclature.
3. On each stockable product: **Kód tovaru (KN)** (*H.S. Code*), **Krajina
   pôvodu** (*Country of Origin*) and the **weight** in kg. A product whose
   commodity code uses a supplementary unit (pieces, litres…) is reported in
   that unit as well.
4. Your company needs its **IČ DPH** (VAT number). Without it the file is not
   generated.
5. On the EU invoices themselves, the OCA module adds the Intrastat fields
   (transaction, transport mode, country); check them before posting.

## Monthly declaration (Community) {#usage}

*Accounting → Reporting → Intrastat → Hlásenie produktov Intrastat*
(*Intrastat Product Declaration*), then *New*:

1. Choose the **year**, **month** and **type** — *Prijatie* (Arrivals) or
   *Odoslanie* (Dispatches). Each flow is its own declaration.
2. **Generovať riadky z faktúr** (*Generate Lines from Invoices*) collects
   the posted invoices and credit notes of the month. The result window lists
   the partners, products, units and invoices it could not use and why. If
   nothing is found, the declaration's
   **Akcia** (*Action*) becomes *Nulové* (nil).
3. Check the **Transakcie** tab (one row per invoice line) and correct
   invoices or products where needed, then generate again.
4. **Potvrdiť** (*Confirm*) groups the transactions into declaration lines —
   one per combination of the reported fields.
5. **Generovať XML súbor** (*Generate XML File*) renders the INSTAT XML,
   validates it against `instat62.xsd`, attaches it to the declaration and
   marks it *Dokončené* (Done). A file that does not validate is refused with
   the schema's error message.
6. Download the file and import it on the INTRASTAT-SK portal
   (`intrastat.financnasprava.sk`), check it there and send it.

What the file contains:

- **One declaration per file** for a first declaration, flow `A` (arrivals)
  or `D` (dispatches), reference period `YYYY-MM`, declaration type `1` (full
  declaration), function code `O` (standard) — or `N` (nil, no items) when
  the declaration's **Akcia** (*Action*) is *Nulové* (*Nil*).
- The reporting unit is your company (VAT number, name, street, post code,
  city). The *declarationId* is the declaration's **Revízia** (*Revision*),
  which is the declaration's sequence number in the month for that flow.
- Per item: commodity code (spaces removed), supplementary unit code and
  quantity, partner country, country of origin, net mass, invoiced value in
  the company currency, the nature of transaction split into its **A and B
  codes** (`11` is filed as A = 1, B = 1), mode of transport, delivery terms
  (Incoterm) and — on dispatches only — the partner's VAT number. Net mass,
  quantity and value are rounded to whole numbers, as the schema requires.
- Supplementary units are filed by their official code (`p/st`,
  `1 000 kWh`, `l alc. 100 %`…), not by the OCA unit name.

**Excel Export** on the declaration gives the same lines as a spreadsheet for
checking.

### Corrections {#corrections}

A declaration already sent is corrected with a **revision**: duplicate the
declaration (it gets the next **Revízia**), set its **Akcia**, generate the
lines and the file again. INTRASTAT-SK numbers a month's declarations per
flow 1, 2, 3 …, and a further file under the next number *adds* to the month
(Statistical Office handbook 2026, para. 221–222), so the action decides what
the file says:

| Akcia | What the file contains |
|---|---|
| *Nahradiť* (*Replace*) | a cancellation (function `D`, no items) of every declaration still standing for the month and flow — those filed since the last earlier *Replace* or *Nil* — followed by the correct items under the revision's number. This is the handbook's way of replacing a declaration (para. 229–230, example 19 b). |
| *Pripojiť* (*Append*) | the revision as a further partial declaration under its number, nothing cancelled. It must hold **only the added transactions**: delete the others from the revision before confirming it. |
| *Nulové* (*Nil*) | the cancellations, as for *Replace*, then a nil declaration (function `N`). |

The cancellation of a declaration carries correction number 1 — each one is
cancelled once.

## Enterprise {#enterprise}

On Odoo Enterprise, [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee)
plays the same role on top of Odoo's own `account_intrastat`. The figures come
from Odoo's Intrastat fields on products and invoices; nothing from the OCA
engine is used.

- **XML button on the report.** *Accounting → Reporting → Dane a fiškálna
  oblasť → Intrastat (Tovar)* (*Taxes & Fiscal → Intrastat (Goods)*) gets an
  **XML** export for a Slovak company. Choose **one calendar month** — a
  longer period is refused. One file holds the arrivals and the dispatches as
  two declarations in one envelope (each flow numbered on its own, so both
  are declaration 1 of the month); a flow you untick in the report's options is left out. A
  month with nothing to declare is refused rather than filed empty.
- **Aggregation.** Odoo's report returns one row per invoice line; the
  module sums rows that agree on every reported field into one item, as
  INSTAT expects. On dispatches, rows for different customer VAT numbers stay
  separate items.
- **Intrastat return.** The module adds a monthly Slovak return *Intrastat*,
  due 15 days after the end of the month, under *Accounting → Accounting →
  Závierka → Zúčtovanie daní* (*Closing → Tax Returns*). Its **Odoslať**
  (*Submit*) step opens a dialog with **Download XML** and the steps on the
  portal; confirming it marks the return as completed. When the return is
  locked, the XML is attached to it.
- The company's VAT number is required; a missing one opens the company form.
  The export must be run with the Slovak company as the active company.

It installs only on Enterprise; it does not need this module.

## Statutory footprint {#footprint}

With [module:l10n_cssk_core](module:l10n_cssk_core) installed alongside the
OCA engine, [module:l10n_cssk_intrastat_footprint](module:l10n_cssk_intrastat_footprint)
installs itself and adds Intrastat to the **Statutory footprint** of a posted
document (see [the footprint](module:l10n_cssk_core#footprint)). For each
Intrastat declaration that took one of the document's lines, the footprint
lists the form *Intrastat*, the period (`YYYY-MM`), the flow and the
declaration's state (*Draft*, *Confirmed*, *Done*), with a link to it. A line
reported in an original and in a corrected declaration lists both.

The footprint reads the link the declaration stored when its lines were
generated. It does not decide whether a line ought to be reported, so **a
month whose declaration has not been generated yet shows nothing**. It works
for both Slovak and Czech OCA declarations; it does not read Odoo
Enterprise's Intrastat report.

Because Odoo installs such bridges only when one of their dependencies is
being installed, a database that already had both modules before the bridge
existed needs it installed once by hand.

## The shared renderer {#engine}

[module:l10n_cssk_intrastat_base](module:l10n_cssk_intrastat_base) holds the
code both editions share and has no screens of its own:

- the **INSTAT XML** builder for Slovakia — one declaration per file for the
  Community path, or one envelope with several declarations for the
  Enterprise path — with validation against the bundled `instat62.xsd`;
- the **InstatOnline CSV** builder for Czechia, used by
  [module:l10n_cz_intrastat_oca](module:l10n_cz_intrastat_oca).

It depends on nothing but `base`, so it installs automatically with whichever
adapter needs it.

## Limitations {#limitations}

- **Item-level corrections are not produced.** A revision replaces whole
  declarations (cancel and refile, see [Corrections](#corrections)); the
  corrective declaration that lists only the changed items under their
  original item numbers (function `M`) is not generated. Both are the
  handbook's procedures.
- The cancellations assume every earlier revision of the month was filed.
  A revision that was never sent is cancelled all the same; delete it rather
  than leave it in the sequence.
- Only the **full declaration** (type `1`) is produced, even when the
  company is set to *Standard*. The simplified procedure is not supported.
- **Region** is filed only when the engine supplies one; no Slovak region
  codes are shipped.
- Thresholds are not checked: the module files what you ask it to file.
- On Enterprise, every export is an original declaration 1 per flow; there
  are no revisions. Two exports for one month are two files numbered alike —
  make corrections of a sent Enterprise declaration on the portal.
- The returned file is what the portal imports; filing and its confirmation
  happen on the portal, outside Odoo.
