=========
Changelog
=========

All notable changes to **l10n_cssk_vies** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Wave 2 external-call hardening: the direct EU VIES REST call runs with request
  timeouts and surfaces transient member-state faults (system down, rate limit)
  as a fault — never silently flipping a partner to *invalid*.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- **Direct EU VIES** on top of core ``base_vat``: calls the European Commission
  VIES REST service directly (per-company opt-in), no Odoo IAP and no Odoo
  account needed.
- **Proof of check**: stores the VIES consultation number (``requestIdentifier``),
  the check timestamp, the VIES request date, and the registered trader name +
  name-match result on the partner.
- A manual **Check VIES (direct)** action and a daily cron refreshing stale
  checks for companies in direct mode.
- CE-clean (``base_vat`` + ``l10n_cssk_core``). Full cs_CZ + sk_SK translations.
