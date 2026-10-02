# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "SK Register Extract (§ 3a, status, activities, filings)",
    "summary": "Keep the register, court and oddiel/vložka as data and compose "
               "the § 3a Obchodného zákonníka sentence from them, instead of "
               "typing it once into the company footer and letting it rot.",
    "description": """
SK Trade Registry Statement (§ 3a)
==================================

§ 3a ods. 1 Obchodného zákonníka requires every business document — invoice,
order, business letter, website — to name the register the subject is entered
in, together with the **oddiel** and **vložka**.

``l10n_sk`` gives ``res.company`` a single free-text ``trade_registry`` field
for that sentence. It is typed once and then forgotten, which is how a company
goes on printing *Okresný súd Bratislava I* years after the registrový súd for
Bratislava became **Mestský súd Bratislava III** on 1. 6. 2023.

This module:

* keeps the three coordinates — **register**, **registrový súd**, **číslo
  zápisu** — as fields on ``res.partner`` (so they can be filled for customers
  and suppliers too, e.g. for contracts);
* composes the § 3a sentence from them, with the Slovak declension the sentence
  needs (locative for the register, genitive for the court);
* keeps ``l10n_sk``'s ``trade_registry`` in step with it, so the sentence
  actually reaches the printed document.

The composed sentence stays **editable** — an override sticks until a
coordinate changes again.

Fill the coordinates from the register automatically by installing
``partner_autocomplete_orsf_sk`` and pointing its Register / Registrový súd /
Číslo zápisu mappings at these three fields.

**Scope note:** the declension is rule-based over a short table of register and
authority prefixes. Anything it does not recognise is passed through verbatim —
a stiff sentence beats a confidently wrong one on a statutory document.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.2.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["account", "l10n_sk", "partner_nace"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_company_views.xml",
        "views/account_move_views.xml",
    ],
    "installable": True,
}
