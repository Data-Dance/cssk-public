=========
Changelog
=========

All notable changes to **account_invoice_ai_extract** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-08-05
-------------------------

Added
~~~~~

- Ported from ``dd_ai_invoice`` 18.0.1.0.0 (``~/Odoo/datadance``) and **renamed**.
  The ``dd_`` brand infix was retired by the 2026-06 naming convention, and the new
  name sits next to Odoo's own ``account_invoice_extract`` so the feature is
  recognisable; ``ai_`` marks the different backend.
- Resolver unit tests (8), which the 18.0 module did not have: VAT normalisation and
  country prefix, tolerance handling on junk input, and every branch of the totals /
  VAT-breakdown reconciliation including the zero-VAT (reverse charge, export) case.

Changed
~~~~~~~

- ``_sql_constraints`` → ``models.Constraint``; Odoo 19 dropped the former from base.
- Models renamed ``dd.ai.invoice.extraction[.run]`` → ``account.invoice.ai.extraction[.run]``
  and ``dd.ai.tax.map`` → ``account.invoice.ai.tax.map``; company fields
  ``dd_ai_invoice_*`` → ``ai_extract_*``.

Migration note
~~~~~~~~~~~~~~

The 18.0 production instance keeps the old module and model names. Upgrading it will
need an openupgradelib ``rename_modules`` + ``rename_models`` + field renames — the
19.0 module deliberately does not carry a migration script, because the rename is a
19.0-only decision and 18.0 is still live.

Not verified here
~~~~~~~~~~~~~~~~~

Install, model creation and the resolver are live-tested on 19.0; the **LLM
round-trip itself was not exercised** (no provider credentials in the test
environment). ``muk_ai`` 19.0.1.10.3 was checked to still expose the three APIs this
module uses: ``provider._request_responses``, ``model._compute_usage_cost``, and the
``muk_ai_attachment`` content block.
