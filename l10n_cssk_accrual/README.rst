==========================================
CZ/SK Estimated Accruals (dohadné položky)
==========================================

Books unbilled items at the period end (e.g. energy consumed in December, the
invoice arriving in January). This is distinct from *časové rozlíšenie /
časové rozlišení* (deferrals) and is shipped by neither Odoo Community nor
Enterprise.

The two countries book such items differently. Czech accounting has
**dohadné účty** 388 / 389 (vyhláška 500/2002) for amounts not supported by all
the documents. Slovak accounting has **no** dohadné účty: **326**
*Nevyfaktúrované dodávky* takes unbilled supplies whose amount the entity
**knows** from a contract or delivery note (§ 50 ods. 6 opatrenia 740/2002); an
uncertain amount is a provision on 323 (§ 50 ods. 3), which this module does not
book; and an unbilled receivable goes on the receivable account it belongs to,
on a separate analytic account (§ 48 ods. 3).

Each estimate carries its own accrual and counterpart account and journal (no
hard-coded chart), so it works for both charts and any custom one. Depends on
**Odoo core only** (``account`` + ``l10n_cssk_core``).

Features
========

* ``cssk.accrual.estimate`` record (mail-tracked, sequenced) with a
  draft → posted → settled / cancelled lifecycle.
* Two estimate types:

  * **Estimated payable**: Dr expense / Cr accrual (CZ 389, SK 326).
  * **Estimated receivable**: Dr accrual (CZ 388, SK an analytic account of the
    receivable) / Cr income.

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
only the difference. **Cancel** reverses a posted estimate. A cancelled estimate
can be **reset to draft**, corrected and posted again: the cancelled entry and
its reversal stay in the books, and posting books a new entry.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
