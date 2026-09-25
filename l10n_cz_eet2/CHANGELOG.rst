=========
Changelog
=========

All notable changes to **l10n_cz_eet2** are documented here.
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

- Sends registered-sale data messages to the Czech EET 2.0 system
  (Elektronická evidence tržeb) over the v4.1 SOAP data interface with WS-Security
  (``lib/eet2_client.py``), returning the FIK / BKP / PKP codes.
- ``eet2.certificate`` model storing and using the taxpayer's signing certificate
  (WS-Security signature; requires ``cryptography``, ``lxml``, ``requests``).
- ``eet2.transaction`` ledger of sent registrations with retry handling and a
  scheduled cron for pending/failed messages (``data/ir_cron.xml``).
- Company / journal / payment configuration for EET registration
  (``res.company``, ``account.journal``, ``account.payment``, config settings) plus
  dedicated menus and security groups/access rules.
