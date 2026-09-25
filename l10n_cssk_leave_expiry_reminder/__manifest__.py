# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Leave Expiry Reminder (CZ/SK)",
    "version": "19.0.1.0.3",
    "category": "Human Resources/Time Off",
    "summary": "Proactively remind employees and HR about expiring "
    "carried-over leave",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": ["hr_holidays"],
    "data": [
        "data/mail_activity_type_data.xml",
        "data/mail_template_data.xml",
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
    ],
    "installable": True,
}
