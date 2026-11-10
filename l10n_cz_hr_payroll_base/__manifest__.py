# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — Payroll Base",
    "version": "18.0.1.3.0",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral base for the Czech payroll: the Czech employee "
    "data (agreement type, taxpayer declaration, children, insurance flags) "
    "and the statutory annual-leave accrual plans, shared by the OCA and the "
    "Enterprise payroll modules.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["cz"],
    # Depends on NEITHER payroll engine: both country modules sit on top of it.
    # hr_contract carries hr.contract (19.0 moved it into hr as hr.version);
    # hr_holidays the accrual plans.
    "depends": [
        "hr_contract",
        "hr_holidays",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/hr_leave_accrual_plan_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "installable": True,
}
