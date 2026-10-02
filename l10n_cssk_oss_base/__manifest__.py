# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK OSS VAT Return — Shared Framework (Union scheme)",
    "version": "19.0.1.0.0",
    "summary": "Country-neutral engine for the quarterly One-Stop-Shop VAT "
               "return (Union scheme): OSS-tagged sales aggregated by member "
               "state of consumption, rate and supply type, converted to EUR "
               "at the ECB rate of the period's last day, with corrections "
               "of earlier quarters. Adds the missing Slovak 5 % rate to "
               "Odoo's OSS tax mapping.",
    "description": """
CZ/SK OSS VAT Return — Shared Framework
=======================================

Builds on Odoo **core** ``l10n_eu_oss``: the per-country *OSS B2C* fiscal
positions and destination-rate sale taxes it creates carry the ``OSS`` tax tag
on every repartition line. This module reads those lines and produces the
content of the OSS return; the Czech (``l10n_cz_oss``, EPO OSSEI1) and Slovak
(``l10n_sk_oss``, DPOSS_EU) layers render and validate the statutory XML.

* ``cssk.oss.return`` — one quarter; rows per member state of consumption ×
  VAT rate × goods/services, corrections of earlier quarters per member
  state, the exchange rates used, export through the shared statutory
  submission pipeline (kontroly → render → XSD → attach → submit).
* The Slovak 5 % rate (since 1. 1. 2025) is missing from core's EU tax map in
  both directions; ``res.company._map_eu_taxes`` adds it without editing core.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": [
        "account",
        "mail",
        "l10n_eu_oss",
        "l10n_cssk_core",
        "l10n_cssk_submission_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_oss_return_version_views.xml",
        "views/cssk_oss_return_views.xml",
        "views/cssk_oss_return_menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
