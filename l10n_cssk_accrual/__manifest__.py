{
    "name": "CZ/SK Estimated Accruals (dohadné položky)",
    "summary": "Estimated unbilled items — book an estimate to the accrual "
               "account (CZ 388/389, SK 326 or a receivable analytic), then "
               "link the actual invoice to true it up.",
    "description": """
CZ/SK Estimated Accruals — dohadné položky
==========================================

Unbilled items at the period end (e.g. energy consumed in December, invoice
arriving in January). Distinct from *časové rozlíšenie* (deferrals), and not
shipped by Odoo CE or EE. The two countries book them differently:

* **CZ** — *dohadné účty* 388 / 389 (vyhláška 500/2002), for amounts not
  supported by all the documents, so not exactly known.
* **SK** — opatrenie 740/2002 has **no** dohadné účty. **326** *Nevyfaktúrované
  dodávky* takes unbilled supplies whose amount the entity **knows** from a
  contract or delivery note (§ 50 ods. 6); an uncertain amount is a provision
  on 323 (§ 50 ods. 3), which this module does not do. An unbilled receivable
  goes on the receivable account it belongs to, on a separate analytic
  account (§ 48 ods. 3).

Workflow (**link & true-up**):

1. **Estimate** — book an estimate as of period end:
   * *Estimated payable*: Dr expense / Cr accrual (CZ 389, SK 326).
   * *Estimated receivable*: Dr accrual (CZ 388, SK a receivable analytic) /
     Cr income.
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
    "version": "19.0.1.1.0",
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
