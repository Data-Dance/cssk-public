# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Company Registry Verification",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.0.0",
    "summary": """
Answer whether an IČO exists in the state register, and say so in a way a gate can act on
    """,
    "description": """
CZ/SK Company Registry Verification
===================================

``l10n_cssk_core`` answers *is this number well-formed?* — the mod-11 check.
This module answers the next question: **does the company exist, and is it
still alive?** It is the step between a valid-looking IČO and a decision that
costs money, such as provisioning a server or approving an account.

The one entry point is::

    env["res.partner"]._cssk_verify_registry(ico, country_code)

It returns a dict whose ``outcome`` is one of:

``invalid``
    Fails the checksum. The register is never asked.
``unsupported``
    No provider is installed for that country.
``absent``
    The register answered, and holds no such subject.
``verified``
    The register answered with the company. ``name``, address, ``tax_id``,
    ``vat`` and ``active`` carry what it said.
``unavailable``
    We could not ask. Outage, timeout or rate limit.

Why ``absent`` and ``unavailable`` are different
------------------------------------------------

They are the whole point of the module. A caller that treats "we could not
reach the register" as "this company does not exist" turns a register outage
into a wall of rejected customers; one that treats it as "verified" opens the
gate every time the register hiccups. **Neither is a safe default for every
caller**, so this module refuses to choose: it reports what happened and each
caller decides. Checkout should fail open — do not lose an order because ORSF
is down. Provisioning should fail closed — never build a machine for a company
nobody could confirm exists.

Providers are discovered, not depended on
-----------------------------------------

``partner_autocomplete_orsf_sk`` (SK) and ``partner_autocomplete_ares_cz`` (CZ)
are looked up in the registry at call time. Neither is a dependency: installing
this module does not drag in the autocomplete stack, and a country with no
provider reports ``unsupported`` rather than failing.

Caching
-------

Answers are cached in ``cssk.registry.lookup`` so a signup burst cannot hammer
the register. ``verified`` and ``absent`` are cached (with different lifetimes
— a company that does not exist yet may exist tomorrow); ``unavailable`` never
is, because caching a failure would extend one outage into a long one.
""",
    "depends": ["l10n_cssk_core"],
    "data": [
        "security/ir.model.access.csv",
        "views/cssk_registry_lookup_views.xml",
    ],
    "installable": True,
}
