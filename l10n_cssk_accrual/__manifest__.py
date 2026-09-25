{
    "name": "CZ/SK Estimated Accruals (dohadné položky)",
    "summary": "Estimated unbilled items — book an estimate to the accrual "
               "account (CZ 388/389, SK 326), then link the actual invoice to "
               "true it up.",
    "description": """
CZ/SK Estimated Accruals — dohadné položky
==========================================

The CZ/SK concept of **dohadné položky / dohadné účty** — items where the
obligation exists but the exact amount is **not yet known** (e.g. energy consumed
in December, invoice arrives in January). Distinct from *časové rozlíšenie*
(deferrals of a known amount), and not shipped by Odoo CE or EE.

Workflow (**link & true-up**):

1. **Estimate** — book an estimate as of period end:
   * *Estimated payable* (nevyfakturovaná dodávka): Dr expense / Cr accrual
     (CZ 389 *dohadné účty pasivní*, SK 326 *nevyfakturované dodávky*).
   * *Estimated receivable*: Dr accrual (CZ 388) / Cr income.
2. **Link the actual invoice** when it arrives (booked normally) and **settle**:
   the estimate is reversed at the invoice date and reconciled against the
   accrual account, so the two net out — only the **difference** remains in the
   new period and the accrual account clears.

Accounts and journal are chosen per estimate (no hard-coded chart), so it works
for both the Czech and Slovak charts and any custom one. Depends on **Odoo core
only** (``account`` + ``l10n_cssk_core``).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.4",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "l10n_cssk_core"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence_data.xml",
        "views/cssk_accrual_estimate_views.xml",
        "views/cssk_accrual_menus.xml",
    ],
    "installable": True,
}
