# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czechia — Wage Surcharges (příplatky) — OCA Payroll",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Statutory Czech wage surcharges (§§ 114–118 zákoníku práce) "
    "as salary rules for the OCA payroll engine.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["cz"],
    "depends": [
        "l10n_cz_hr_payroll_oca",
        "l10n_cz_hr_payroll_priplatky",
    ],
    "data": [
        "data/hr_salary_rule_data.xml",
    ],
    "installable": True,
}
