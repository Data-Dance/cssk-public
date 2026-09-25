==========================================
CZ/SK Estimated Accruals (dohadné položky)
==========================================

Implements the CZ/SK concept of **dohadné položky / dohadné účty** — items where
the obligation exists but the exact amount is **not yet known** (e.g. energy
consumed in December, the invoice arriving in January). This is distinct from
*časové rozlíšenie / časové rozlišení* (deferrals of a *known* amount) and is
shipped by neither Odoo Community nor Enterprise.

Each estimate carries its own accrual and counterpart account and journal (no
hard-coded chart), so it works for the Czech chart (388/389), the Slovak chart
(326 *nevyfakturované dodávky*) and any custom one. Depends on **Odoo core only**
(``account`` + ``l10n_cssk_core``).

Features
========

* ``cssk.accrual.estimate`` record (mail-tracked, sequenced) with a
  draft → posted → settled / cancelled lifecycle.
* Two estimate types:

  * **Estimated payable** (dohadný účet pasívny): Dr expense / Cr accrual
    (CZ 389, SK 326).
  * **Estimated receivable** (dohadný účet aktívny): Dr accrual (CZ 388) /
    Cr income.

* **Link & true-up** settlement — link the actual invoice when it arrives; the
  estimate is reversed at the invoice date and reconciled against the
  (reconcilable) accrual account, so the accrual clears and only the difference
  stays in the new period.
* Per-estimate accounts and journal — no chart assumptions; CZ, SK and custom
  charts all supported.

Usage
=====

*Accounting ▸ Accounting ▸ Estimated Accruals (dohadné).* Create an estimate at
period end: pick the type, partner, amount, description, journal, accrual account
and counterpart account, then **Post** to book the entry. When the real invoice
arrives (booked normally), open the estimate, select it in *Actual Invoice* and
**Settle** — the estimate is reversed at the invoice date and reconciled, leaving
only the difference. **Cancel** reverses a posted estimate; a posted estimate
must be cancelled before it can be reset to draft.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
