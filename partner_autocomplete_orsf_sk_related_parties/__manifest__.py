# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Autocomplete using ORSF SK — Related Parties (závislé osoby)",
    "summary": "Pull one partner's ownership/officer graph from ORSF on demand, "
               "so § 17 ods. 5 related-party transactions can be recognised "
               "instead of remembered.",
    "description": """
ORSF SK — Related Parties (závislé osoby)
=========================================

§ 17 ods. 5 zákona o dani z príjmov subjects transactions between **závislé
osoby** to transfer-pricing documentation. Nothing in an Odoo database knows
which partners are related to your company or to each other, so in practice the
question gets answered from memory — or not at all, until a daňová kontrola
asks.

ORSF's graph endpoint answers it mechanically: the natural persons holding a
role in a company, and the other companies those persons are attached to.

This module adds a **Related parties** tab to the contact, a per-partner
*Fetch from register* button, and an ``orsf.sk.related.party`` row for each
edge found — keeping the IČO and name even when the counterpart is not a
contact in this database, which it usually is not.

Two things it deliberately does not do
--------------------------------------

**No bulk fetching.** ORSF gates persons and graphs behind a signed-in session
and cites GDPR Art. 6(1)(f), *mass profiling prevention*, with the instruction
"never bulk-fetch persons". So this is one button on one partner. There is no
cron, no batch server action and no list-view multi-select — that is a design
constraint, not a missing feature.

**No session on anything else.** ORSF issues no API key for persons and
graphs, so the provider signs in with the ORSF account e-mail and password set
in Settings and caches the session. That session is presented **only** on the
graph request. Autocomplete, lookups and search stay anonymous, because ORSF's
published per-minute limits for signed-in tiers are lower than the anonymous
one — enabling this module must not slow down type-ahead for the whole database.

The password sits in ``ir.config_parameter``, which is **plain text in the
database and in every backup**. Use a dedicated ORSF account, never a personal
one.

Status
------

**The graph response shape is unverified.** ORSF's OpenAPI spec documents the
endpoint's security and parameters but gives no schema for its body — only
"nodes + edges (graphology-compatible JSON)". The parser accepts the dialects
graphology emits (``key``/``id``, nested or flattened ``attributes``) and skips
anything it does not recognise, so a shape change costs coverage rather than
correctness. Confirm it against a real signed-in response before relying on the
output; correcting it means editing ``_orsf_sk_parse_graph``.

Being *related* in the register is also not the same as being a **závislá
osoba** under § 17 ods. 5 — the statutory test covers economic and personal
connection, not only a shared officer. Treat the output as a shortlist for an
accountant, never as the conclusion.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.2.0.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["partner_autocomplete_orsf_sk", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/orsf_sk_related_party_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
}
