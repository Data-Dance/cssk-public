from odoo.addons.purchase_order_advance_invoice.tools import (
    apply_purchase_advance_spec,
)

# Slovak chart wiring for the received-advance flow.
# Account codes resolved against the installed l10n_sk chart (chart_template = 'sk').
SK_SPEC = {
    "journal_code": "PDADV",
    "journal_name": "Faktúry k odoslaným platbám",
    # The standard SK chart has 314000 (Poskytnuté preddavky) but no
    # reconcilable clearing account, so we ship one. Payable type: it is the
    # payment-term leg of the received tax document.
    "create_accounts": [
        {
            "code": "314001",
            "name": "Poskytnuté preddavky – zúčtovanie (daňový doklad)",
            "account_type": "liability_payable",
            "reconcile": True,
        },
    ],
    "accounts": {
        "paid_clearing": "314001",  # reconcilable clearing / transit
        "paid_st": "314000",        # Poskytnuté preddavky (short-term)
        "paid_lt": "",              # no 47x mirror on the asset side
    },
}


def _l10n_sk_purchase_advance_post_init(env):
    apply_purchase_advance_spec(env, "sk", SK_SPEC)
