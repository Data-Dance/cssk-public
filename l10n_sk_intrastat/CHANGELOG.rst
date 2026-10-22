=========
Changelog
=========

All notable changes to **l10n_sk_intrastat** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: INTRASTAT-SK country layer on the OCA ``intrastat_product`` 19.0 declaration engine (CE-clean). The engine collects intra-EU goods movements and computes the grouped declaration lines; this module renders them as the official Finančná správa INTRASTAT-SK **INSTAT (instat62)** XML via ``l10n_cssk_intrastat_base``.
- AGPL-3 (subclasses the AGPL OCA engine); the shared INSTAT renderer is LGPL-3 so the EE variant can reuse it without inheriting AGPL.
