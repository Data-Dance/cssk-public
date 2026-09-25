==================================================
SK Účtovné vzory — predkontácie interných dokladov
==================================================

Named MD/D patterns for **interné doklady** on the Slovak chart of accounts
(``l10n_sk``), built on the OCA journal-entry template engine
(``account_move_template``). The accountant picks a pattern, types one amount,
and gets a balanced draft entry.

What this is not
================

The word *predkontácia* is ambiguous, and the ambiguity matters here.

In POHODA, ABRA Gen, Money S3 and Omega a predkontácia is an attribute **of a
document**. ABRA defines it per document type and even per document series, it
is offered for selection on the document, and posting the document (*zaúčtovanie*)
derives the MD/D lines from it. It is the system's mechanism for automated
posting of source documents.

**This module is not that, and neither is the engine underneath it.**
``account_move_template`` has no link to any document: it never touches
``account.move`` except to ``create()`` one. The arrow points the other way —
in ABRA the document selects the predkontácia, here the predkontácia produces a
new document. Afterwards nothing but a chatter message records the connection.

What this module covers is therefore the **interný doklad** slice: entries that
have no source document to derive anything from. That slice is real, and it is
the one Odoo genuinely had nothing for.

Where the rest of the predkontácia surface lives in Odoo
========================================================

For invoices, bank and cash, Odoo automates posting too — it just *derives* the
accounts instead of letting you *declare* them, and the ruleset is spread over
several objects rather than concentrated in one named list:

===================================  ==========================================
Predkontácia would decide…           …in Odoo it comes from
===================================  ==========================================
Invoice line account                 product / product category income+expense,
                                     remapped by the fiscal position
Receivable / payable leg             partner ``property_account_receivable_id``
                                     / ``property_account_payable_id``, also
                                     fiscal-position mapped
DPH accounts                         the tax's repartition lines
Bank / cash statement counterpart    ``account.reconcile.model``
Fallback account                     ``account.journal.default_account_id``
Inventory postings                   stock valuation accounts (Method A family)
===================================  ==========================================

A consequence worth planning for: migrating a customer's predkontácia list into
Odoo is a **conversion exercise, not a lift-and-shift**. A list of sixty
predkontácie decomposes into product categories, fiscal positions, partner
accounts and tax repartitions; only the leftover internal ones become records
in this module.

Starter set
===========

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

Install on a database using the Slovak chart of accounts. Two menus, both from
the OCA engine:

**Maintain the patterns** — *Fakturácia ▸ Konfigurácia ▸ Účtovníctvo ▸ Účtovné
vzory (predkontácie)*. Requires the *Billing Administrator*
(``account.group_account_manager``) group. The six shipped patterns are already
in that list and are freely editable.

**Post an entry** — *Fakturácia ▸ Účtovníctvo ▸ Vytvoriť zápis podľa vzoru*.
Pick a pattern, press *Ďalej*, type the amount, press *Vytvoriť účtovný zápis*.
The same wizard is reachable from the *Vytvoriť účtovný zápis* button on the
pattern's own form.

The entry is created **in draft** — the engine never posts it, so the normal
review-and-post control is untouched.

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
