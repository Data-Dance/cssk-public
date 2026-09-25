from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

# Slovak chart wiring for the advance-invoice flow.
# Account codes resolved against the installed l10n_sk chart (chart_template = 'sk').
SK_SPEC = {
    "journal_code": "TDADV",
    "journal_name": "Faktúry k prijatým platbám",
    # The standard SK chart has 324000 (Prijaté preddavky) but no reconcilable
    # clearing account, so we ship one.
    "create_accounts": [
        {
            "code": "324001",
            "name": "Prijaté preddavky – zúčtovanie (daňový doklad)",
            "account_type": "asset_receivable",
            "reconcile": True,
        },
    ],
    "accounts": {
        "received_clearing": "324001",  # reconcilable clearing / transit
        "tax_doc_st": "324000",         # Prijaté preddavky (short-term)
        "tax_doc_lt": "475000",         # Dlhodobé prijaté preddavky (long-term)
    },
}


def _l10n_sk_advance_post_init(env):
    apply_advance_invoice_spec(env, "sk", SK_SPEC)
