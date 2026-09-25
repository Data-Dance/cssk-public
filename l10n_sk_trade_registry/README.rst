====================================
SK Trade Registry Statement (§ 3a)
====================================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| Keep the register coordinates as data and compose the § 3a sentence from them.

**Table of contents**

.. contents::
   :local:


Why
===

§ 3a ods. 1 Obchodného zákonníka requires every business document — invoice,
order, business letter, website — to name the register the subject is entered
in, together with the **oddiel** and **vložka**.

``l10n_sk`` gives ``res.company`` one free-text ``trade_registry`` field for
that sentence. It gets typed once and then forgotten, which is how a company
goes on printing *Okresný súd Bratislava I* years after the registrový súd for
Bratislava became **Mestský súd Bratislava III** on 1. 6. 2023.


What it adds
============

On ``res.partner`` (and mirrored onto ``res.company``):

#. **Register** — Obchodný register, Živnostenský register, …
#. **Registrový súd** — Mestský súd Bratislava III, or an Okresný úrad for a
   živnostník
#. **Číslo zápisu** — Sro/3586/B
#. **§ 3a statement** — composed from the three, editable

The composed sentence is copied into ``l10n_sk``'s ``trade_registry``, which is
the field the external layout actually prints.


How the composer behaves
========================

* The register goes into the **locative** (*v Obchodnom registri*), the
  authority into the **genitive** (*Mestského súdu Bratislava III*), from a
  short table of fixed prefixes. The place name keeps the nominative form the
  register itself uses.
* **Zapísaná** for a company, **Zapísaný** for a sole trader.
* ``oddiel`` / ``vložka`` wording is used **only** for the Obchodný register —
  that is its own vocabulary. A Živnostenský register number can contain a
  slash too, and labelling its parts that way would put words on a statutory
  document that the issuing register does not use.
* Anything the tables do not recognise passes through **verbatim**. A slightly
  stiff sentence is a much better failure than a confidently wrong one.


Register status
===============

The register also says whether the subject still exists, and that is worth
keeping rather than glancing at once in an autocomplete dropdown:

#. **Stav v registri** — aktívna / pozastavená / zrušená / vymazaná / neznámy
#. **Dátum zániku**
#. **Register checked** — a status is only worth as much as its date
#. **Not trading** — computed, true for zrušená, vymazaná or pozastavená

A contact the register no longer shows as trading carries a banner, is muted in
the contact list, and can be listed through *Zrušené subjekty (SK)*. Any invoice
or bill for one raises a warning; on a **vendor bill** it adds that the
deduction is in question, which is the more expensive direction of the mistake.

The warning **never blocks**. Documents get booked for dissolved subjects
legitimately — a final invoice, a late credit note, a bill that arrives after
the counterparty wound up. The date on the document decides that, not the
register's state today.

An unrecognised status parses to nothing rather than to ``unknown``: "we did
not understand the answer" and "the register says it does not know" are
different facts, and only the second is the register's.

Ownership of ``trade_registry``
===============================

The module records what it last wrote, so it can tell its own output apart from
wording a person typed:

* wording typed by a person is **never overwritten**, including at create time
  and after a later coordinate change;
* a sentence the module wrote **is** kept in step — and is **cleared** when the
  coordinates are cleared, because stale statutory text on an invoice is the
  failure this module exists to prevent.


Filling it from the register
============================

Install ``partner_autocomplete_orsf_sk``. It fills the register coordinates,
the status, the dissolution date and the check timestamp on every enrichment —
by feature detection, so neither module depends on the other.


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
