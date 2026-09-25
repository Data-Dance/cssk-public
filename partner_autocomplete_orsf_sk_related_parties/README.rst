===========================================
ORSF SK — Related Parties (závislé osoby)
===========================================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| One partner's ownership / officer graph from ORSF, on demand.

**Table of contents**

.. contents::
   :local:


Why
===

§ 17 ods. 5 zákona o dani z príjmov subjects transactions between **závislé
osoby** to transfer-pricing documentation. Nothing in an Odoo database knows
which partners are related to your company or to each other, so in practice the
question is answered from memory — or not at all, until a daňová kontrola asks.

ORSF's graph endpoint answers it mechanically: the natural persons holding a
role in a company, and the other companies those persons are attached to.


What it adds
============

A **Related parties (SK)** tab on the contact, a *Fetch from register* button,
and an ``orsf.sk.related.party`` row per edge found — degree 1 for a person
holding a role in this partner, degree 2 for another company that person is
also attached to. The IČO and name are kept even when the counterpart is not a
contact in this database, which it usually is not; where it is, the row links
to it.


Two things it deliberately does not do
======================================

**No bulk fetching.** ORSF gates persons and graphs behind a signed-in session
and cites GDPR Art. 6(1)(f) — *mass profiling prevention* — with the
instruction "never bulk-fetch persons". So this is one button on one partner.
There is no cron, no batch server action and no list-view multi-select. The
``ensure_one`` in the action is what enforces it, and it is load-bearing.

**No session on anything else.** The session is presented only on the graph
request. Autocomplete, ``/lookup``, ``/lookup/batch``, ``/search`` and
``/refresh`` all go out anonymously — see *Configuration* for why.

Configuration
=============

ORSF issues **no API key** for persons and graphs; the only scheme its OpenAPI
document defines for them is a *better-auth* session cookie
(``__Secure-orsf.session_token``, HttpOnly, never displayed). So the provider
signs in for you:

#. Create a **dedicated** ORSF account — not a personal one.
#. Enter it in *Settings ▸ Contacts ▸ ORSF* as **ORSF account e-mail** and
   **ORSF account password**.

``partner_autocomplete_orsf_sk`` then posts those to
``https://orsf.sk/api/auth/sign-in/email`` when a session is needed, caches the
token for 12 hours, and on a 401 signs in once more and retries once. The
password is never logged, and a refused sign-in logs only the status code.

**The password is plain text** in ``ir.config_parameter`` — in the database
and in every backup. That is the weakest part of this module, and the reason it
is better treated as a consultant's tool than a customer-facing feature until
ORSF offers machine credentials for these endpoints.

**Why the session goes nowhere else.** Anonymous ``/lookup`` measures
600 requests a minute per IP. ORSF's published tiers are slower per minute —
FREE 60, PRO 300; only TEAM reaches 600 (pricing page, read 2026-09-06). If the
session rode along on every request, configuring this module could move a
database's whole type-ahead onto the account's lower limit, and trigger a
sign-in on a keystroke whenever the cached session had lapsed. So only
``_orsf_get(..., authenticated=True)`` carries it, and an anonymous 401 never
triggers a sign-in. Whether ORSF actually applies the account tier to a request
that merely carries a session is **not verified**; the code does not rely on the
answer either way.


Status — read this before relying on it
=======================================

**The graph response shape is unverified.** ORSF's OpenAPI spec documents the
endpoint's security and its ``depth`` parameter but gives **no schema** for the
response body — only "nodes + edges (graphology-compatible JSON)". The endpoint
is gated, so there is no anonymous sample to check against.

The parser therefore accepts the dialects graphology actually emits
(``key``/``id``, ``attributes`` nested or flattened) and **skips anything it
does not recognise**, so a shape mismatch costs coverage rather than
correctness — an unrecognised body yields no rows, not wrong rows. The tests
pin that documented behaviour against synthetic payloads; they do not prove the
parser matches ORSF's live output.

Confirm it against a real signed-in response before relying on the output.
Correcting it means editing ``_orsf_sk_parse_graph`` and nothing else.

**Being related in the register is not the same as being a závislá osoba.**
§ 17 ods. 5 covers economic and personal connection, not only a shared officer.
Treat the output as a shortlist for an accountant, never as the conclusion.


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
