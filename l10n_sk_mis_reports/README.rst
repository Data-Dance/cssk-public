==================================
SK Manažérske výkazy (MIS Builder)
==================================

Management reporting for **Community**. Enterprise ships an executive summary and
a cash-flow report in ``account_reports``; Community has neither, which left
"management reporting (mng P&L, cash flow)" as the last open item on the customer
requirement list this collection was built against.

What it ships
=============

A **manažérska výsledovka** on the ``l10n_sk`` chart, as an OCA ``mis_builder``
template — so it is a starting point the controller edits, and periods,
comparisons, budgets and XLSX export all come from the engine.

It reads trieda 5 and 6 by account-code pattern, so it needs no tagging:

* tržby — tovar / vlastné výrobky a služby / ostatné výnosy
* náklady — predaný tovar, spotreba, služby, osobné náklady, dane a poplatky,
  odpisy, ostatné
* **prevádzkový výsledok**
* finančné výnosy a náklady → **výsledok pred zdanením**
* daň z príjmov → **výsledok po zdanení**

Revenue is negated on the way in so every line reads positive and the subtotals
add up the way a reader expects.

Not the statutory statements
============================

This is the *management* view, deliberately separate:

* the **Výkaz ziskov a strát** filed with the účtovná závierka is in
  ``l10n_sk_fs`` (UZPODv14, XSD-validated);
* the statutory **Prehľad peňažných tokov** is there too;
* ``mis_builder_cash_flow`` is a treasury **forecast** (due dates + manual
  forecast lines) — a third, different thing again.

Do not reconcile this line by line against the statutory ones: the groupings are
chosen for readability, not for the Opatrenie MF SR.

Gotcha worth knowing
====================

A KPI name must not begin with an accounting-expression prefix (``bal``,
``balp``, ``crd``, ``deb``…). MIS Builder rewrites those tokens textually, so a
helper KPI named ``balp_54_55`` became ``(AccountingNone)_55`` and every
expression referencing it failed with ``#ERR``. It is called ``trieda_54_55``.

Honesty flag
============

The account groupings are a management choice, not a statutory mapping, and want
accountant sign-off — particularly which accounts belong in *ostatné náklady*
rather than an operating group.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see LICENSE) — it depends on the AGPL MIS Builder engine.
