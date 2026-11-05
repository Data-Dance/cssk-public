# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop the Slovak and Czech names of the analysis from before 1.5.1.

1.5.1 renamed "Book vs Tax Depreciation" to "Depreciation Analysis", next to
the "Accounting vs Tax Depreciation" comparison it was easily taken for. An
upgrade rewrites the English of the menu and the action but loads the
catalogues without overwriting, so the old names would stay. This removes a
translation only while it is still the one this module shipped; the catalogue
load that follows this script fills in the new one. A name a user typed in is
left alone.
"""

MODULE = "account_asset_tax_oca"
OLD = {
    "sk_SK": "Účtovné vs. daňové odpisy",
    "cs_CZ": "Účetní vs. daňové odpisy",
}
RECORDS = (
    ("ir_ui_menu", "ir.ui.menu", "menu_asset_book_tax_report"),
    ("ir_act_window", "ir.actions.act_window", "action_asset_book_tax_report"),
)


def migrate(cr, version):
    for table, model, xmlid in RECORDS:
        for lang, old in OLD.items():
            cr.execute(
                f"""UPDATE {table} t SET name = t.name - %s
                     FROM ir_model_data d
                    WHERE d.module = %s AND d.name = %s AND d.model = %s
                      AND d.res_id = t.id AND t.name ->> %s = %s""",
                [lang, MODULE, xmlid, model, lang, old],
            )
