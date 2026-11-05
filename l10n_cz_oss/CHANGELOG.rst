=========
Changelog
=========

All notable changes to **l10n_cz_oss** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- Declines ``l10n_cz_statutory``'s competent-office check: OSSEI1 has no
  ``c_ufo``; the special schemes are administered by one office for everyone.

Added
~~~~~

- EPO **OSSEI1** export of the OSS return (režim EU): ``VetaD`` / ``VetaP`` /
  ``VetaR`` / ``VetaO``, validated against ``ossei1_epo2.xsd`` (structure
  01.01.04), pinned in ``data/SCHEMA_VERSION``.
- Export preflight: the filer must have a Czech DIČ (CZ + 8–10 digits).

[19.0.1.0.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak and Czech catalogues: translated the strings that were still English.
