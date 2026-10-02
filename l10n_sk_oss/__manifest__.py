# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK OSS VAT Return (DPOSS_EU — úprava pre Úniu)",
    "version": "19.0.1.0.0",
    "summary": "Slovak layer of the OSS return: the Finančná správa eForm "
               "DPOSS_EUv01 XML (daňové priznanie k DPH — osobitná úprava "
               "pre Úniu), on the EU OSSVATReturnMSCON schema, XSD-validated.",
    "description": """
SK OSS VAT Return — DPOSS_EUv01
===============================

Renders the quarterly OSS return computed by ``l10n_cssk_oss_base`` as the
Finančná správa eForm **DPOSS_EUv01** ("Daňové priznanie k DPH - Úprava pre
Úniu"). Its XML is the EU-wide ``OSSVATReturnMSCON`` structure
(``urn:ec.europa.eu:taxud:frsr:vatunion:v1.0``): supplies from the member
state of identification and from establishments elsewhere, corrections of
earlier quarters, grand totals, per-member-state balances and the total VAT
due. Validated against the official ``dposs_eu01.xsd`` before it is attached.

Only the Union scheme is covered — the scheme Odoo's ``l10n_eu_oss`` taxes
implement. The non-Union and import schemes are not built.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_oss_base", "l10n_sk"],
    "data": [
        "report/dposs_eu_templates.xml",
        "data/sk_oss_version_data.xml",
    ],
    "installable": True,
}
