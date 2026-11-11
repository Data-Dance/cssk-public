# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank feeds — journal header",
    "summary": "One header on the bank journal form where every bank feed "
               "(Tatra banka Premium API, Fio, …) puts its actions.",
    "description": """
Bank feeds — journal header
===========================

Core's ``account.journal`` form has no ``<header>``, so each bank feed hid
its *Pull* buttons somewhere in the form body — the Tatra banka ones inside
their own tab, where nobody looked for them. This module adds one empty
``<header name="bank_feed">`` to the form, shown on bank journals only, and
every feed puts its buttons there::

    <xpath expr="//header[@name='bank_feed']" position="inside">
        <button name="action_x_pull" type="object" string="Pull transactions"/>
    </xpath>

No models, no settings, no dependencies beyond ``account``.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": ["views/account_journal_views.xml"],
    "installable": True,
}
