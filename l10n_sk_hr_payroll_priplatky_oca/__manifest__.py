# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Wage Surcharges (príplatky) — OCA payroll",
    "version": "19.0.1.0.2",
    "category": "Human Resources/Payroll",
    "summary": "Statutory Slovak wage surcharges and the minimum-wage top-up "
    "as salary rules for the OCA payroll engine.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["sk"],
    "depends": [
        "l10n_sk_hr_payroll_oca",
        "l10n_sk_hr_payroll_priplatky",
    ],
    "data": [
        "data/hr_salary_rule_data.xml",
    ],
    "auto_install": True,
    "installable": True,
}
