====================================
Partner Autocomplete ORSF SK
====================================

.. |badge1| image:: https://raster.shields.io/badge/license-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

| Completes Partner information from the Slovak state registers via https://orsf.sk
|
| Available countries

#. Slovakia


| Information that can be completed:

#. Name and address (street, city, PSČ, country)
#. IČ DPH into ``vat`` — only while the registration is live
#. IČO into ``company_registry``
#. Company type (company vs sole trader)
#. With the sibling modules installed, straight into their own fields:

   * DIČ — ``l10n_sk_base``
   * Register, registrový súd, číslo zápisu, stav, dátum zániku, predmety
     podnikania, účtovné závierky, predchádzajúce názvy a sídla —
     ``l10n_sk_trade_registry``
   * Druh registrácie DPH (§) and Platiteľ DPH od — ``l10n_sk_vat_registration``
#. Dynamically mappable (see Configuration point 5.) — only the values with no
   field of their own:

   * SK NACE
   * Právna forma
   * Veľkostná kategória
   * Dátum vzniku


**Table of contents**

.. contents::
   :local:


Why ORSF
========

ORSF aggregates the Slovak state registers — RPO, ORSR, ŽRSR, RÚZ and the
Finančná správa VAT-payer list — behind one JSON API. For the endpoints this
module uses it needs **no API key, no account and no subscription**, which is
what separates it from the other Slovak providers in this family
(``partner_autocomplete_finstat``, ``partner_autocomplete_slovensko_digital``).

The trade-off is that ORSF is a **community aggregator in beta with no SLA**,
not an authoritative source: it is right for filling a contact form, and wrong
as evidence for a filing. Where a statutory answer is needed, ask the authority
— VIES for a VAT number (``l10n_cssk_vies``), the Finančná správa lists for
supplier reliability (``l10n_sk_payment_reliability``).


Configuration
=============

#. Go to *Settings > General Settings > Contacts*
#. Enable *Partner Autocomplete*
#. Choose provider **ORSF.SK**
#. Adjust the base URL and timeout only if you run a mirror; the defaults point
   at ``https://api.orsf.sk/v1`` with a 15 s timeout, and a base URL that is
   not ``http(s)://`` is refused
#. Review the three behaviour switches — fill Company ID, set company type,
   format PSČ — all on by default and stored per company
#. Choose fields for mapping (optional)

|
| Dynamically mappable fields paste register values into any field of the
  Contact (``res.partner``) model. Leaving one empty simply skips that value.


How the lookup behaves
======================

* Typing a **name** searches ORSF's fulltext index and offers the first five
  hits, each labelled ``Name (IČO)``. A subject the register no longer shows as
  active carries its status — ``— zrušená``, ``— pozastavená`` — in the label,
  so a defunct IČO is not picked by accident.
* Typing an **IČO** (6-8 digits) reads the register directly rather than going
  through the fulltext index — via ``/lookup/{ico}``, which carries exactly the
  identity fields the dropdown needs at ~1 KB instead of ~100 KB, and allows
  **600 requests/minute where the full record allows 30**.
* Typing a **VAT number** resolves it through ORSF's exact DIČ index (a Slovak
  IČ DPH is ``SK`` + the DIČ) and then **confirms the hit against the company
  record** — holding a DIČ is not holding an IČ DPH, and a ``mode: dic`` hit
  reports ``icDph: null`` even for a live payer. If that finds nothing it falls
  back to the fulltext index, keeping only an exact IČ DPH match; the fuzzy
  index answers a VAT query with lexical neighbours, which are dropped.
* ``vat`` is filled **only while the register still shows a live VAT
  registration**. ORSF keeps the historical registration row after a
  deregistration; writing that lapsed IČ DPH onto an invoice is exactly what
  makes VIES reject it.
* Anonymous rate limits are **600/min on ``/lookup``** and **30/min on
  ``/companies``** and ``/search``. A 429, a timeout or an outage degrades to
  "no suggestions", never to an error in the user's form.
* An optional **Bearer token** raises the quota and unlocks a sole trader's
  full address, which ORSF otherwise withholds (``addressLocked``). It is a
  token, not a password — see *Authentication* below.


Autocomplete During Import
==========================

#. Create an import file with columns: *name* and *import_enrich_company*
   (it can have other columns as well)
#. In the *import_enrich_company* column, enter the IČO
#. Import the file


Manual Update of Records
=========================

#. Go to *Contacts*
#. Switch to the list view
#. Select records you want to update
#. Click *Action > Update*


Authentication — and what is never asked for
============================================

Everything this module does works **anonymously**. Two optional tokens exist,
and neither is an account password:

``orsf_sk.api_token``
    A **Bearer token** from an ORSF account. Raises the request quota and
    unlocks the full address of a sole trader.

``orsf_sk.session_token``
    The value of the ``__Secure-orsf.session_token`` cookie from an
    administrator's own signed-in browser session — a *better-auth* session
    token that expires by itself. Only the gated person and graph endpoints
    need it, and nothing in **this** module calls those;
    ``partner_autocomplete_orsf_sk_related_parties`` does.

An ORSF account password is never asked for, stored or transmitted.

Where the fields come from
==========================

Three places, and the third is optional:

**Odoo core** — ``name``, ``street``, ``city``, ``zip``, ``country_id``,
``vat`` (``base_vat``), ``company_registry`` (which ``l10n_sk`` labels IČO) and
``company_type``.

**The dispatcher** — ``partner_gid`` and ``partner_autocomplete_provider``,
from ``partner_autocomplete_dispatcher``, this module's only dependency.

**The SK sibling modules, detected at runtime rather than depended on** — the
same move ``partner_autocomplete`` itself makes for ``base_address_extended``:

``l10n_sk_base``
    ``l10n_sk_dic`` — DIČ.
``l10n_sk_trade_registry``
    Register coordinates, status, dissolution date, and the predmety
    podnikania / účtovné závierky / previous-names lists.
``l10n_sk_vat_registration``
    § 4 / § 7 / § 7a category and *platiteľ DPH od*.

Feature detection is what keeps this a Tools module with no accounting or
localisation weight: it installs and works on its own. **The consequence is
that without those siblings, the values they own are simply not stored** —
they are no longer offered as mappings, because a mapping into an arbitrary
field would give you a copy that nothing else in the stack understands. Install
the sibling that owns the data you want.

Known limits
============

* **Sole-trader search needs an ORSF account.** ``kind=sole_trader`` returns
  401 anonymously. A živnostník is still reachable by IČO and still appears in
  an unfiltered name search.
* **Persons and the ownership graph are gated.** ``/persons`` and ``/graph``
  need a session cookie; ORSF issues no API keys yet, so this module does not
  use them.
* **Financial statements come back as metadata only.** The RÚZ filings on a
  company record carry periods, filing dates and PDF attachment descriptors —
  no numeric ``obsah``.
* **ORSF's documentation page understates its own API.** The OpenAPI document
  at ``/v1/openapi.json`` is readable anonymously and describes ``/lookup``,
  ``POST /lookup/batch``, ``GET /companies`` and ``GET /tiers``, none of which
  the docs page lists — and it contradicts the page on tokens, which the page
  says do not exist. Where they disagree, the spec and the live response
  headers have been right.
* ORSF's ``mode: dic`` search hits report ``icDph: null`` even for a live
  payer. The module therefore never trusts a search hit for the VAT number; it
  re-reads the company record during enrichment.


Attribution
===========

ORSF data is published under **CC-BY 4.0**. A deployment that republishes the
data must credit ORSF and the source registers (RPO / ORSR / ŽRSR / RÚZ / FS).
The Settings panel carries that credit.


Author
======

* Data Dance s.r.o.

Contact
=======
https://www.datadance.eu/
