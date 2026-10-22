===============================
SK Predkontácie (účtovné vzory)
===============================

Thin country layer between the Slovak chart of accounts (``l10n_sk``) and the OCA
journal-entry template engine (``account_move_template``). It ships a small starter
set of Slovak *predkontácie* — named MD/D patterns that an accountant picks from a
wizard, enters one amount, and posts — resolved against the Slovak chart.

Starter set:

* **Prevod peňazí cez účet 261** (peniaze na ceste), both legs, both directions —
  výber z pokladnice (261/211), príjem na bankový účet (221/261), výber z
  bankového účtu (261/221), vklad do pokladnice (211/261).
* **Preúčtovanie výsledku hospodárenia** po schválení — zisk (431/428) and
  strata (429/431).

New companies receive the templates when the SK chart loads (via the chart
template); existing SK companies get them on install (post-init hook), through the
same loader, so the xmlids match either way.

The hook loads only what a company does not already have. That makes it
idempotent, and — the reason that matters — it means **an edit the accountant
made to a shipped predkontácia is never reverted**: these are editable data
records, and the chart loader rewrites any record it is handed.

It is licensed **AGPL-3** because it depends on the AGPL OCA template engine.

Features
========

* Slovak predkontácie as ordinary, editable ``account.move.template`` records on
  the l10n_sk chart.
* One-amount postings: the first line is typed by the accountant, every further
  line mirrors it through the engine's ``L1`` formula.
* Slovak names, shipped directly rather than as ``name@sk`` translations of an
  English source: ``account.move.template.name`` is not a translatable field, and
  the chart loader's ``@lang`` mechanism only covers models in ``TEMPLATE_MODELS``.

Usage
=====

Install on a database using the Slovak chart of accounts, then
*Accounting ▸ Accounting ▸ Journal Entry Templates*. Pick a predkontácia, press
*Generate Journal Entry*, enter the amount, and the balanced entry is created in
the general journal.

Scope note
==========

The starter set is deliberately minimal and mechanically indisputable. A real
deployment's predkontácie follow that company's own *vnútorná smernica*, so the
intended workflow is to extend the set per customer — ideally by mining the
predkontácie out of the customer's previous accounting system rather than
inventing them.

The account mapping wants the same **accountant sign-off** as the other statutory
mappings in this collection.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
