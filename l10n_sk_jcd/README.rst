========================================
SK JCD — dovoz tovaru (colné vyhlásenie)
========================================

The Slovak import customs declaration (*colné vyhlásenie*, historically JCD) as an
accounting document. It ties together the three things an import scatters:

1. **Clo a colné poplatky** — capitalised into the stock value of the received
   goods through a ``stock.landed.cost`` (and therefore, on Method A, posted
   through the perpetual seams by ``stock_account_method_a_landed``).
2. **Daň pri dovoze** — posted so it lands on the correct DPH rows automatically.
3. **The customs document itself** — recorded, with the VAT deduction gated on it.

Two VAT regimes, both already in the chart
==========================================

============================================ ================== ==========================
Regime                                       l10n_sk tax        DPH rows
============================================ ================== ==========================
Daň zaplatená colnému orgánu                 ``vs_cust_*``      deduction r22 / r22a / r23
§ 84a ods. 3 — samozdanenie pri dovoze       ``vs_imp_post_*``  base r11c–e, tax r12c–e,
                                                                deduction r23a–c
============================================ ================== ==========================

This module reimplements none of that. It selects the right core tax and lets the
existing tag-driven ``l10n_sk_vat_return`` engine report it. Rate mapping (verified
against ``account.tax-sk.csv`` and the DPHv25 poučenie, body 38 and 38a):
r22 = 19 %, r22a = 5 %, r23 = 23 %.

The deduction gate
==================

Per the DPHv25 poučenie bod 38 (§ 49 ods. 2 písm. d)), the platiteľ may deduct
*"ak pri odpočítaní dane má dovozný doklad potvrdený colným orgánom, v ktorom je
platiteľ uvedený ako príjemca alebo dovozca."*

The declaration therefore **refuses to post** until the MRN is recorded and the
confirmed customs document is attached. This is the rule in this area that is
routinely got wrong, and it is cheap to enforce.

Posting shape
=============

Nothing is bought from the customs office — the taxable amount at import is
notional. The document posts the base **twice** on a clearing account, once
positive (carrying the tax) and once negative, so only the VAT and the duty
remain real. The ``vs_cust_*`` base repartition carries no DPH tag, so the
notional base reaches no row of the return; under § 84a it deliberately does
(r11c–e), which is why the same shape serves both.

Limitations and honesty flags
=============================

* **Landed costs require FIFO or AVCO costing.** Odoo refuses to apply them on
  standard-cost products, so duty capitalisation only works for categories using
  a real cost method. Asserted by the test fixture.
* The **VAT base** defaults to colná hodnota + clo + iné poplatky (§ 24) — the
  ordinary case, not the only one. It is editable, and wants accountant sign-off
  along with the account mapping.
* Whether a consignment falls under § 84a ods. 3 is a **registration status**, not
  a per-shipment choice; the selector merely defaults from the company setting.
* The declaration is an **accounting** document. It does not file anything with
  the customs authority and has no eCustoms/eDovoz connection.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
