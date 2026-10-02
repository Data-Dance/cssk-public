# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czechia — Wage Surcharges (příplatky) — Base",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral statutory wage surcharges for overtime, public "
    "holiday, night, weekend and difficult-environment work (§§ 114–118 "
    "zákoníku práce), plus the minimum wage and the top-up to it.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["cz"],
    # Only core hr: the arithmetic, the rate tables and the contract fields
    # must install without either payroll engine. The two bridge modules
    # (_oca, _dd) add the salary rules.
    "depends": [
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_cz_minimum_wage_data.xml",
        "data/l10n_cz_wage_surcharge_rate_data.xml",
        "views/l10n_cz_minimum_wage_views.xml",
        "views/l10n_cz_wage_surcharge_rate_views.xml",
        "views/hr_version_views.xml",
        "views/l10n_cz_priplatky_menus.xml",
    ],
    "installable": True,
}
