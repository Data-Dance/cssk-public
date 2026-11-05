# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MIS Builder Column Breakdown",
    "version": "19.0.1.1.1",
    "summary": "Split a MIS Builder column into one column per journal, partner, "
               "company, product or any other field, with a total.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Reporting",
    "depends": ["mis_builder"],
    "data": ["views/mis_report_instance_views.xml"],
    "installable": True,
}
