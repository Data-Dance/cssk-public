=========
Changelog
=========

All notable changes to **l10n_sk_oss** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- Finančná správa **DPOSS_EUv01** export of the OSS return (úprava pre Úniu):
  the EU ``OSSVATReturnMSCON`` XML with the ``vun:`` prefix the eForm loader
  needs, validated against ``dposs_eu01.xsd``, pinned in
  ``data/SCHEMA_VERSION``.
- Export preflight: the filer must have a Slovak IČ DPH (SK + 10 digits).
