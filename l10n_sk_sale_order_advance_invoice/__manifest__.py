{
    "name": "Advance Invoices - Slovak Localization",
    "version": "19.0.1.1.0",
    "summary": "Slovak chart wiring for advance invoices (preddavkové faktúry)",
    "description": """
Slovak localization of Advance Invoices
=========================================

Wires the country-neutral ``sale_order_advance_invoice`` module to the Slovak
chart of accounts. On install it configures, for every company on the Slovak
chart template:

* the dedicated tax-documents journal (Faktúry k prijatým platbám),
* the reconcilable advance-clearing account **324001** (created — the standard
  chart has no reconcilable clearing account),
* the short-term received-advance account **324000** (Prijaté preddavky),
* the long-term received-advance account **475000** (Dlhodobé prijaté preddavky).

Existing manual configuration is preserved (only empty fields are filled).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["sale_order_advance_invoice", "l10n_sk"],
    "data": [],
    "post_init_hook": "_l10n_sk_advance_post_init",
    "installable": True,
    "auto_install": False,
}
