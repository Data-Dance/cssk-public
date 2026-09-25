{
    "name": "SK Invoice (statutory PDF)",
    "summary": "Slovak invoice layout: DIČ/IČO/IČ DPH party block, payment "
               "symbols, supply/issue/due dates and mandatory §74 statutory "
               "phrases (reverse charge, exemptions). Language-driven labels.",
    "description": """
SK Invoice — statutory PDF
==========================

Turns Odoo's generic invoice into a Slovak ``faktúra`` that carries the
mandatory content of §74 of the Slovak VAT Act, on top of what core +
``l10n_sk`` already render (IČO, trade registry, delivery date, VAT breakdown,
PAY by square QR, signature).

Adds:

* **Party identifiers** — customer **DIČ** next to the IČ DPH / IČO core already
  prints.
* **Payment symbols** — variabilný / konštantný / špecifický symbol (from
  ``l10n_cssk_core``).
* **Statutory phrases** — auto-detected and printed in Slovak (+ English gloss):
  domestic reverse charge (*prenesenie daňovej povinnosti*, §69/12), intra-EU
  supply (§43) and export (§47) exemptions; plus a free-text manual note.

Labels are **language-driven** — Slovak for SK-language partners, English
otherwise — via standard Odoo translations; the statutory phrases always carry
Slovak because the law requires it.

**Note:** the phrase auto-detection is a best-effort heuristic (zero-rate +
partner country + a per-tax reverse-charge flag). Have an accountant confirm the
mapping for your tax setup; a manual note field is provided for edge cases.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.3",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "l10n_cssk_core", "l10n_sk_base", "l10n_cssk_payment_symbols"],
    "data": [
        "views/account_tax_views.xml",
        "views/account_move_views.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
