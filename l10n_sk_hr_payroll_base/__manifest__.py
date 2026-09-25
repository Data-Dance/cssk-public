# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Payroll Base (employment forms)",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral base for the Slovak payroll: the employment "
    "forms (pracovný pomer, DoVP, DoPČ, DoBPŠ) and one table saying which "
    "contributions and entitlements apply to which of them.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["sk"],
    # Depends on NEITHER payroll engine: both country modules sit on top of it.
    "depends": [
        "hr",
    ],
    "installable": True,
}
