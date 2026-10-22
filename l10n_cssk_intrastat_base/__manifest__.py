# Copyright 2026 Data Dance s.r.o.
# License LGPL-3 — see the LICENSE file.
{
    "name": "CZ/SK Intrastat — INSTAT XML builder (base)",
    "summary": "Edition-neutral INTRASTAT-SK INSTAT (instat62) XML renderer "
               "shared by the CE (OCA) and EE (account_intrastat) adapters.",
    "description": """
Dependency-free INSTAT (instat62) XML builder for INTRASTAT-SK
==============================================================
Provides ``cssk.instat.builder.build_instat_xml(header, lines)`` which renders
the official Finančná správa INTRASTAT-SK message from a normalized header +
line dicts. No dependency on the OCA intrastat engine or Odoo EE
``account_intrastat`` — so it is LGPL-3 and can be imported by the AGPL CE
adapter (``l10n_sk_intrastat``) and the proprietary EE adapter alike.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "18.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["base"],
    "installable": True,
}
