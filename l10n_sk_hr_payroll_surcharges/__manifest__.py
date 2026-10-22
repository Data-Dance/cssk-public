# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Wage Surcharges (príplatky) — Base",
    "version": "18.0.1.2.0",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral statutory wage surcharges for night, Saturday, "
    "Sunday, public-holiday, overtime, difficult-conditions and standby work "
    "(§§ 121–123 Zákonníka práce), plus the six stupne náročnosti minimum "
    "wage claims and the top-up to them.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["sk"],
    "depends": [
        # hr_contract, not plain hr: the surcharge inputs live on hr.contract
        # here (they are core hr on 19.0, where it is hr.version).
        "hr_contract",
        "l10n_sk_hr_payroll_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_sk_minimum_wage_data.xml",
        "data/l10n_sk_wage_surcharge_rate_data.xml",
        "views/l10n_sk_minimum_wage_views.xml",
        "views/l10n_sk_wage_surcharge_rate_views.xml",
        "views/hr_contract_views.xml",
        "views/hr_job_views.xml",
        "views/l10n_sk_priplatky_menus.xml",
    ],
    "installable": True,
}
