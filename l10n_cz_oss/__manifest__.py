# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ OSS VAT Return (DAP OSS — režim EU, OSSEI1)",
    "version": "19.0.1.0.0",
    "summary": "Czech layer of the OSS return: the EPO Pisemnost/OSSEI1 "
               "XML (daňové přiznání k DPH ve zvláštním režimu jednoho "
               "správního místa — režim Evropské unie), XSD-validated.",
    "description": """
CZ OSS VAT Return — OSSEI1
==========================

Renders the quarterly OSS return computed by ``l10n_cssk_oss_base`` as the EPO
form **OSSEI1** ("DAP OSS - režim EU - Přiznání k DPH platné od 1.7.2021"):
``VetaD`` / ``VetaP``, one ``VetaR`` per member state × rate × goods/services
and one ``VetaO`` per corrected quarter and member state. Validated against the
official ``ossei1_epo2.xsd`` before it is attached.

Only the Union scheme (režim EU) is covered — it is the scheme Odoo's
``l10n_eu_oss`` taxes implement. The non-Union (OSSNI1) and import (OSSII1)
schemes are separate EPO forms and are not built.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_oss_base", "l10n_cz"],
    "data": [
        "report/ossei1_templates.xml",
        "data/cz_oss_version_data.xml",
    ],
    "installable": True,
}
