# Copyright 2026 Data Dance s.r.o.
# License AGPL-3 — see the LICENSE file.
{
    "name": "Czechia — INTRASTAT-CZ (CE / OCA)",
    "summary": "INTRASTAT-CZ Celní správa InstatOnline CSV on the OCA "
               "intrastat_product engine (CE-clean). EE uses Odoo EE "
               "l10n_cz_intrastat instead.",
    "description": """
INTRASTAT-CZ — Community / OCA adapter
======================================
Thin country layer on the OCA ``intrastat_product`` declaration engine: the
engine collects intra-EU goods movements and computes the grouped declaration
lines; this module renders them as the official **Celní správa InstatOnline CSV**
(the file uploaded at celnisprava.gov.cz → InstatOnline) via
``l10n_cssk_intrastat_base``.

The CSV column layout, constant fields and number formatting reproduce the
official Odoo EE ``l10n_cz_intrastat`` output (validated against its expected
file in the shared base's tests). The Czech declaration has **no XSD** — the
InstatOnline portal validates on upload.

**Module name** — this is the Community/OCA adapter; it is intentionally NOT
named ``l10n_cz_intrastat`` to avoid colliding with Odoo Enterprise's native
module of that name (which an EE customer uses instead). One edition installs
exactly one of the two.

AGPL-3 because it depends on (subclasses) the AGPL OCA engine. The shared CSV
renderer lives in the LGPL-3 ``l10n_cssk_intrastat_base``.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["intrastat_product", "l10n_cssk_intrastat_base", "l10n_cz"],
    "installable": True,
}
