=========
Changelog
=========

All notable changes to **l10n_cssk_public_holidays** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-10-27
-------------------------

Added
~~~~~
- Slovak (zákon č. 241/1993 Z. z.) and Czech (zákon č. 245/2000 Sb.) days of
  rest generated into the OCA public holiday calendar per year and country,
  including the Slovak exceptions: 1. 9. up to 2023, 17. 11. up to 2024, and
  8. 5. and 15. 9. as working days in 2026 (§ 4b, zákon č. 261/2025 Z. z.).
- The current and the next year are loaded at install, and a monthly scheduled
  action keeps them present. Generation is idempotent and keeps manual edits.
