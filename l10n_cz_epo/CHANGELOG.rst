=========
Changelog
=========

All notable changes to **l10n_cz_epo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-29
-------------------------

Added
~~~~~

- EPO as a submission channel: filings signed with the company's qualified
  certificate (PKCS#7 signedData, DER) and sent to the Podatelna EPO
  interface — to check them in test mode, or, where the company allows it,
  to file them; the potvrzení and podací číslo are kept and the state is
  polled to acceptance or rejection.
- EPO certificates, readable only by the filing group.
- A filing with an unknown outcome is not retried, so it cannot be filed
  twice; EPO's answers are parsed without DTDs or entities.
