# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Vehicle Logbook and Travel Orders",
    "summary": "Trip log per vehicle and domestic and foreign travel orders "
               "with statutory meal, pocket money, kilometre and fuel reimbursement.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["fleet", "hr_expense", "l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/l10n_sk_travel_rate_data.xml",
        "data/l10n_sk_travel_foreign_rate_data.xml",
        "data/product_data.xml",
        "data/ir_sequence_data.xml",
        "views/l10n_sk_vehicle_trip_views.xml",
        "views/l10n_sk_travel_order_views.xml",
        "views/l10n_sk_travel_rate_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
}
