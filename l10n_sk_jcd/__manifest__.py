# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK JCD — dovoz tovaru (colné vyhlásenie)",
    "summary": "Slovak import customs declaration: duty into stock value, "
               "import VAT onto the right DPH rows, deduction gated on the "
               "confirmed customs document.",
    "description": """
SK JCD — dovoz tovaru
=====================

The Slovak import customs declaration (*colné vyhlásenie*, historically JCD) as
an accounting document. It ties together the three things an import scatters:

1. **Clo a colné poplatky** — capitalised into the stock value of the received
   goods through a ``stock.landed.cost``, so the landed cost of imported stock is
   right (and, on Method A, posted through the perpetual seams).
2. **Daň pri dovoze** — posted so it lands on the correct DPH rows automatically.
3. **The customs document itself** — recorded, with the VAT deduction **gated** on
   it (see below).

Two VAT regimes, both already modelled by the ``l10n_sk`` chart
--------------------------------------------------------------

* **Daň zaplatená colnému orgánu** (``vs_cust_19/5/23``) — the VAT is assessed and
  paid to the customs office and only deducted: rows **r22 / r22a / r23**.
* **§ 84a ods. 3 — samozdanenie pri dovoze** (``vs_imp_post_19/5/23``) — self
  assessed: base **r11c / r11d / r11e**, tax **r12c / r12d / r12e**, deduction
  **r23a / r23b / r23c**.

This module does **not** reimplement any of that. It selects the right core tax
and lets the existing tag-driven ``l10n_sk_vat_return`` engine report it.

The deduction gate
------------------

Per the DPHv25 poučenie (bod 38, § 49 ods. 2 písm. d)): the platiteľ may deduct
*"ak pri odpočítaní dane má dovozný doklad potvrdený colným orgánom, v ktorom je
platiteľ uvedený ako príjemca alebo dovozca."* The declaration therefore refuses
to post the deduction until the confirmed customs document is attached and the
MRN recorded. That is the one rule in this area that is routinely got wrong, and
it is cheap to enforce.

Posting shape
-------------

The taxable amount at import is notional — nothing is bought from the customs
office — so the VAT document posts the base **twice** on a clearing account,
once positive (carrying the tax) and once negative, leaving only the VAT and the
duty as real amounts. The ``vs_cust_*`` base repartition carries no DPH tag, so
the notional base reaches no row.

Honesty flags
-------------

* The **VAT base** defaults to colná hodnota + clo + iné poplatky (§ 24), which is
  the ordinary case but not the only one — it is editable, and wants accountant
  sign-off along with the account mapping.
* Whether a given consignment falls under § 84a ods. 3 at all is a **registration
  status**, not a per-shipment choice; the regime selector defaults from the
  company setting.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.4",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_sk", "stock_landed_costs", "purchase_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/product_data.xml",
        "views/l10n_sk_jcd_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
