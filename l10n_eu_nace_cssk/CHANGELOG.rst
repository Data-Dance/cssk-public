=========
Changelog
=========

All notable changes to **l10n_eu_nace_cssk** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **A Slovak five-digit NACE code gets its Rev. 2 industry.** SK NACE Rev. 2
  stays in the Slovak register until 2028 and Slovakia's Rev. 2.1 has no fifth
  digit, but Rev. 2.1 was tried first, so a class reused in Rev. 2.1 with
  another meaning gave the wrong industry. A national subclass now matches only
  contacts of its own country.

[19.0.1.0.0] — 2026-09-29
-------------------------

Added
~~~~~

- First release.
