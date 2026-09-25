from odoo.addons.purchase_order_advance_invoice.tools import (
    apply_purchase_advance_spec,
)

# Czech chart wiring for the received-advance flow.
# Account codes resolved against the installed l10n_cz chart (chart_template = 'cz').
CZ_SPEC = {
    "journal_code": "PDADV",
    "journal_name": "Daňové doklady k odeslaným platbám",
    # The standard CZ chart has 314000 (Poskytnuté provozní zálohy) but no
    # reconcilable clearing account, so we ship one. Payable type: it is the
    # payment-term leg of the received tax document.
    "create_accounts": [
        {
            "code": "314001",
            "name": "Poskytnuté zálohy – zúčtování (daňový doklad)",
            "account_type": "liability_payable",
            "reconcile": True,
        },
    ],
    "accounts": {
        "paid_clearing": "314001",  # reconcilable clearing / transit
        "paid_st": "314000",        # Poskytnuté provozní zálohy (short-term)
        "paid_lt": "",              # no 47x mirror on the asset side
    },
}


def _l10n_cz_purchase_advance_post_init(env):
    apply_purchase_advance_spec(env, "cz", CZ_SPEC)
