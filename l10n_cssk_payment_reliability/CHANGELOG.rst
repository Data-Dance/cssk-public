=========
Changelog
=========

All notable changes to **l10n_cssk_payment_reliability** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Wave 2 external-call hardening on the shared supplier-check spine: register
  lookups performed by the country providers now run with request timeouts and
  surfaced errors, so a register outage degrades gracefully rather than hanging
  the bill.

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Country-neutral base for the CZ/SK **supplier reliability check** (guarantor
  liability — ručenie za daň §69/14 SK, ručení §109 CZ): on a vendor bill it
  checks the supplier's tax reliability and whether the bank account being paid
  is one registered/published with the tax authority.
- Result **snapshotted onto the bill** (status + registered accounts + timestamp)
  as point-in-time proof, with a chatter warning; it **never blocks** the
  payment. Actual register lookups live in the country providers
  (``l10n_sk_payment_reliability`` …).
- CE-clean (Odoo core ``account`` + ``l10n_cssk_core``). Full cs_CZ + sk_SK
  translations.
