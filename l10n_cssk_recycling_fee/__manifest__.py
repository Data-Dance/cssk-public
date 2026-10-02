# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Recycling Fee (recyklační příspěvek / recyklačný poplatok)",
    "version": "19.0.1.0.0",
    "summary": "Dated CZ/SK recycling-fee rates on OCA ecotax classifications, "
    "the statutory per-line 'z toho recyklační příspěvek' on the invoice, and "
    "a per-category period report for the collective scheme.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account_ecotax", "report_xlsx"],
    "data": [
        "security/ir.model.access.csv",
        "data/account_ecotax_category_data.xml",
        "data/ir_cron_data.xml",
        "views/account_ecotax_classification_views.xml",
        "views/res_config_settings_views.xml",
        "views/recycling_fee_report_views.xml",
        "report/recycling_fee_xlsx.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
