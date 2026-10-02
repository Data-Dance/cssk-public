# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Autocomplete using ORSF SK",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.3.0",
    "summary": """
Completes Partner information from the Slovak state registers via https://orsf.sk
    """,
    "description": """
Partner Autocomplete using ORSF SK
==================================

Registers ``partner.autocomplete.provider.orsf_sk`` ("ORSF.SK") into the
``partner_autocomplete_dispatcher`` registry.

ORSF (https://orsf.sk) aggregates the Slovak state registers — RPO, ORSR, ŽRSR,
RÚZ and the Finančná správa VAT-payer list — behind one free JSON API. Unlike
``partner_autocomplete_finstat`` and ``partner_autocomplete_slovensko_digital``
it needs **no API key and no subscription** for the endpoints this module uses.

What it fills in
----------------

* Name, street, city, PSČ, country
* IČ DPH into ``vat`` — **only when the register still shows a live VAT
  registration**, so a deregistered payer does not get a stale VAT number
* IČO into ``company_registry`` (and into any field you map)
* ``company_type`` from the register's ``kind`` (company vs sole trader)
* Optional mappings for DIČ, SK NACE, legal form, register number and office,
  incorporation and dissolution dates, size band, VAT-registration paragraph
  and the date VAT registration started

Attribution
-----------

ORSF data is published under **CC-BY 4.0**. Deployments that republish the data
must credit ORSF and the source registers (RPO / ORSR / ŽRSR / RÚZ / FS).
""",
    "depends": ["partner_autocomplete_dispatcher"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
