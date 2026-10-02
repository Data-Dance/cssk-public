# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "KB BEST Format — shared builders and parser",
    "summary": "Komerční banka BEST client format: domestic and foreign/SEPA "
               "payment files out, electronic statements in.",
    "description": """
Single source of truth for Komerční banka's **BEST** fixed-width client format
(MojeBanka Business, Profibanka, Přímý kanál):

* ``utils.best.build_best_domestic`` — domestic payment batch (úhrady and
  inkasa, record ``01``);
* ``utils.best.build_best_foreign`` — foreign and SEPA payment batch (``02``
  with the ``03`` structured address);
* ``utils.best.parse_best_statement`` — electronic statement (``*.OKM``,
  ``51``/``52`` records) into the OCA statement-import triplets.

No models — pure helpers imported via
``odoo.addons.account_kb_best_base.utils.best``. The edition shims are
``account_payment_kb_best`` (OCA payment order) and
``account_statement_import_kb_best`` (OCA statement import).
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_cz_bankfile_base"],
    "installable": True,
}
