from . import models
from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

# Czech chart wiring for the advance-invoice flow.
# Account codes resolved against the installed l10n_cz chart (chart_template = 'cz').
CZ_SPEC = {
    "journal_code": "TDADV",
    "journal_name": "Daňové doklady k přijatým platbám",
    # The standard CZ chart has 324000 (Přijaté provozní zálohy) but no reconcilable
    # clearing account, so we ship one.
    "create_accounts": [
        {
            "code": "324001",
            "name": "Přijaté zálohy – zúčtování (daňový doklad)",
            "account_type": "asset_receivable",
            "reconcile": True,
        },
    ],
    "accounts": {
        "received_clearing": "324001",  # reconcilable clearing / transit
        "tax_doc_st": "324000",         # Přijaté provozní zálohy (short-term)
        "tax_doc_lt": "475000",         # Dlouhodobé přijaté zálohy (long-term)
    },
}


def _l10n_cz_advance_post_init(env):
    apply_advance_invoice_spec(env, "cz", CZ_SPEC)
