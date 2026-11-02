# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Currency Rate Update SK",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "18.0.1.2.0",
    "category": "Financial Management/Configuration",
    "description": """
    The module updates currency rates from Slovakian banks, 
    Available banks:
    Tatra banka(up-to-date and historical data up to 30 days, ONLY Foreign currency middle)
    VÚB banka(up-to-date data),
    """,
    "depends": ["base", "currency_rate_update"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
}
