{
    "name": "Advance Invoices - Czech Localization",
    "version": "19.0.1.0.0",
    "summary": "Czech chart wiring for advance invoices (zálohové faktury)",
    "description": """
Czech localization of Advance Invoices
=======================================

Wires the country-neutral ``sale_order_advance_invoice`` module to the Czech
chart of accounts. On install it configures, for every company on the Czech
chart template:

* the dedicated tax-documents journal (Daňové doklady k přijatým platbám),
* the reconcilable advance-clearing account **324001** (created — the standard
  chart has no reconcilable clearing account),
* the short-term received-advance account **324000** (Přijaté provozní zálohy),
* the long-term received-advance account **475000** (Dlouhodobé přijaté zálohy).

Existing manual configuration is preserved (only empty fields are filled).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["sale_order_advance_invoice", "l10n_cz"],
    "data": [],
    "post_init_hook": "_l10n_cz_advance_post_init",
    "installable": True,
    "auto_install": False,
}
