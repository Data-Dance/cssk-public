# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia Base Localization",
    "summary": "The Slovak DIČ — the income-tax identifier, which is not the "
               "VAT number and not the company registry number.",
    "description": """
Slovakia base localization
==========================

Slovakia issues **three** identifiers where most countries manage with two:

* **IČO** — company registry number (Odoo's ``company_registry``)
* **DIČ** — the income-tax identifier, ten digits — **this module**
* **IČ DPH** — the VAT number, ``SK`` + the DIČ (Odoo's ``vat``)

A subject can hold a DIČ and no IČ DPH at all: anyone registered for income tax
who is not a VAT payer. That is why the DIČ needs a field of its own.

**Czech Republic is a different case and needs no such field.** In Czech usage
*DIČ* simply is the VAT number (``CZ`` + IČO), so ``vat`` already holds it, and
a separate field there would print the same number twice on a document.

Migrating from ``l10n_cssk_core``
---------------------------------

This field used to be ``l10n_cssk_dic`` in the shared CZ/SK base, on the
premise that both countries needed it. Installing this module carries existing
values over automatically; the old column is left untouched.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.2.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk"],
    "countries": ["sk"],
    "data": [
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
