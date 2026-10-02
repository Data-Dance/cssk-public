# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "KB XML SEPA Credit Transfer",
    "summary": "Komerční banka's profile of the OCA pain.001.001.03 SEPA "
               "credit transfer: structured postal address, SWIFT character "
               "set.",
    "description": """
Komerční banka's XML format for foreign payments (*Klientský formát XML SEPA
CT v KB*) is ISO 20022 pain.001.001.03, which OCA
``account_banking_sepa_credit_transfer`` already generates. This module
adapts its output to what KB documents, for orders paid from a KB account:
the structured postal address KB reads (``StrtNm``/``BldgNb``/``PstCd``/
``TwnNm``/``Ctry``, left out without town and country) and the SWIFT
character set. Other banks' orders are untouched.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Accounting",
    "version": "19.0.1.0.0",
    "depends": ["account_banking_sepa_credit_transfer", "account_cz_bankfile_base"],
    "license": "AGPL-3",
    "installable": True,
}
