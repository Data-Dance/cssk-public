# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
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
``account_intrastat``, so nothing here is bound by OEEL and the module is ours
alone to license: the same builder serves the AGPL Community adapter
(``l10n_sk_intrastat``) and, under our own commercial licence, an Enterprise
one.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["base"],
    "installable": True,
}
