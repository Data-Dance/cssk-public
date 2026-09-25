=========
Changelog
=========

All notable changes to **l10n_cssk_registry_verify** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-07
-------------------------

Added
~~~~~

- First release. ``res.partner._cssk_verify_registry(ico, country_code)`` asks
  the state register whether a company exists and reports what happened, as
  one of ``invalid`` / ``unsupported`` / ``absent`` / ``verified`` /
  ``unavailable``.
- ``cssk.registry.lookup`` caches answers so a public signup form cannot
  hammer the register. ``verified`` (24 h) and ``absent`` (1 h) are cached;
  ``unavailable`` never is.

Notes
~~~~~

- **The module decides nothing, and that is the design.** ``absent`` ("the
  register holds no such subject") and ``unavailable`` ("we could not ask")
  are different answers and no single default is safe for both callers:
  checkout should fail **open**, because losing an order to an ORSF outage is
  worse than accepting an unverified IČO that a human will see anyway;
  provisioning should fail **closed**, because building a machine for a
  company nobody could confirm exists is how a hosting platform becomes an
  abuse platform.
- ``partner_autocomplete_orsf_sk`` grew ``_orsf_probe`` for exactly this:
  ``_orsf_get`` collapses 404, timeout, rate limit and a refused login all to
  ``None``, which is correct for a type-ahead and unusable for a gate.
- **CZ is ``unsupported`` for now, deliberately.**
  ``partner_autocomplete_ares_cz`` swallows every exception into an empty
  dict, so it cannot tell "no such company" from "ARES is down". Wiring it up
  before it can would make the gate silently wrong rather than visibly
  incomplete.
- Providers are discovered in the registry at call time, not depended on, so
  installing this does not drag in the autocomplete stack.
