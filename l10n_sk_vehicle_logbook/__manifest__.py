# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Vehicle Logbook and Travel Orders",
    "summary": "Trip log per vehicle and domestic and foreign travel orders: "
               "approval before the trip, advance, settlement after it with the "
               "statutory meal, pocket money, kilometre and fuel reimbursement.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.2.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["fleet", "hr_expense", "hr_expense_advance_clearing", "l10n_sk"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/l10n_sk_travel_rate_data.xml",
        "data/l10n_sk_travel_foreign_rate_data.xml",
        "data/product_data.xml",
        "data/ir_sequence_data.xml",
        "data/mail_activity_type_data.xml",
        "views/l10n_sk_vehicle_trip_views.xml",
        "views/l10n_sk_travel_order_views.xml",
        "views/l10n_sk_travel_rate_views.xml",
        "views/hr_expense_views.xml",
        "report/travel_order_report.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
