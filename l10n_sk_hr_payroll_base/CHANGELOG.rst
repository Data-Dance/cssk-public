=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.0.0 (2026-08-03)
-----------------------

* Initial release.
* ``applicability`` — one table stating which contributions and entitlements
  apply to which of the four Slovak employment forms, and under which income
  regularity. Odoo-free, so it reads and diffs as the statement of law it is.
* ``hr.version.l10n_sk_applies(concept)`` — reachable from a salary-rule
  condition on either engine, since both hand the version to every rule.
* An unknown concept raises. Returning a default would let a typo look like a
  legal answer, and every caller is deciding whether to charge or pay someone.
