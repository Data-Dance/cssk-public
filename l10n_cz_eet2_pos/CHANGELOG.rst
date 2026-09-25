=========
Changelog
=========

All notable changes to **l10n_cz_eet2_pos** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Registers Point-of-Sale payments with the Czech EET 2.0 system, extending
  ``l10n_cz_eet2`` into POS.
- Per-payment-method EET flag on ``pos.payment.method`` and EET settings on
  ``pos.config``; ``pos.order`` carries the registration and its returned codes.
- Prints the POK (potvrzení o evidenci — proof of registration) on the receipt via
  a POS receipt template override.
