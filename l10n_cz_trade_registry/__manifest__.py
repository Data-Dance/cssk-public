# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ Register Extract (§ 435, status, activities)",
    "summary": "Keep the veřejný rejstřík, rejstříkový soud and spisová "
               "značka as data and compose the § 435 občanského zákoníku "
               "statement from them, instead of typing it once into the "
               "company and letting it rot.",
    "description": """
CZ Trade Registry Statement (§ 435)
===================================

§ 435 odst. 1 občanského zákoníku (zákon č. 89/2012 Sb.) requires every
entrepreneur to state on business documents (*obchodní listiny*) and on the
website the name and seat, and — when entered in the obchodní rejstřík — the
entry **včetně oddílu a vložky**. One entered in another veřejný rejstřík
states that entry; one entered in no public register states the entry in
another evidence (a živnostník: the živnostenský rejstřík).

``l10n_cz`` gives ``res.company`` a single free-text ``trade_registry`` field
for that, printed on the invoice. It is typed once and then forgotten.

This module:

* keeps the three coordinates — **rejstřík**, **rejstříkový soud**,
  **spisová značka** (oddíl and vložka) — as fields on ``res.partner`` (so
  they can be filled for customers and suppliers too, e.g. for contracts);
* composes the statement from them, in a wording that needs no grammatical
  gender of the subject;
* keeps ``l10n_cz``'s ``trade_registry`` in step with it, so the statement
  actually reaches the printed invoice;
* stores what the register says about a partner — status, date of
  establishment and of dissolution, scope of business, previous names and
  seats — and warns on a document whose counterparty is no longer active.

The composed statement stays **editable** — an override sticks until a
coordinate changes again.

Fill everything from the register automatically by installing
``partner_autocomplete_ares_cz`` (19.0.1.4.0 or later), which maps ARES's copy
of the veřejný rejstřík onto these fields.

**Scope note:** the wording is rule-based over the six veřejné rejstříky of
zákon č. 304/2013 Sb. and the courts that keep them. Anything it does not
recognise is passed through verbatim — a stiff statement beats a confidently
wrong one on a statutory document.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "l10n_cz"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/account_move_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
