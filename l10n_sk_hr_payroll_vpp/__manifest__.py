# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — VPP insurance statement for work agreements",
    "version": "18.0.1.0.1",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Slovak social-insurance statement for work agreements / "
               "irregular income (VPP/VPP2026) filed to the Sociálna poisťovňa — "
               "aggregate summary + per-employee annex, XML validated against "
               "VPP-v2026.xsd. Engine-neutral (payroll or the hr_payroll "
               "engine).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/vpp_templates.xml",
        "data/vpp_version_data.xml",
        "views/l10n_sk_vpp_views.xml",
    ],
    "installable": True,
}
