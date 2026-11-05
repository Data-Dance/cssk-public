# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop the Slovak and Czech names of the comparison screen from before 1.11.1.

1.11.1 renamed "Tax Depreciation Reconciliation" to "Accounting vs Tax
Depreciation" in English and in both catalogues. An upgrade rewrites the
English of the menu, the action and the report, but loads the catalogues
without overwriting, so the old "Rekonciliácia daňových odpisov" stayed. This
removes a translation only when it is still the one this module shipped; the
catalogue load that follows this script fills it in afresh. A name a user
typed in is left alone.
"""

OLD = {
    "sk_SK": ("Rekonciliácia daňových odpisov", "Rekonciliácia daňových odpisov (DPPO)"),
    "cs_CZ": ("Rekonciliace daňových odpisů", "Rekonciliace daňových odpisů (DPPO)"),
}
RECORDS = (
    ("ir_ui_menu", "ir.ui.menu", "menu_account_asset_tax_reconciliation"),
    ("ir_act_window", "ir.actions.act_window", "action_account_asset_tax_reconciliation"),
    ("ir_act_report_xml", "ir.actions.report", "action_report_reconciliation"),
)


def migrate(cr, version):
    for table, model, xmlid in RECORDS:
        for lang, old in OLD.items():
            cr.execute(
                f"""UPDATE {table} t SET name = t.name - %s
                     FROM ir_model_data d
                    WHERE d.module = 'account_asset_tax' AND d.name = %s AND d.model = %s
                      AND d.res_id = t.id AND t.name ->> %s IN %s""",
                [lang, xmlid, model, lang, old],
            )
