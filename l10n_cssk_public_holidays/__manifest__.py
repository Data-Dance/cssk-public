# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Public Holidays: Slovakia and Czech Republic",
    "summary": "Generates the Slovak and Czech days of rest into the OCA public "
    "holiday calendar, year by year, with the statutory exceptions, and keeps "
    "the Slovak ones as public holidays of the working calendars.",
    "version": "19.0.1.0.2",
    "category": "Human Resources/Time Off",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": ["calendar_public_holiday", "resource"],
    "data": [
        "data/ir_cron.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
