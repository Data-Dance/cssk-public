=========
Changelog
=========

18.0.1.1.0 (2026-08-08)
=======================

* **Fixed: an irregular-income dohodár was registered with the wrong
  relationship code.** ``typ_zec`` keyed on the agreement type alone, so a DoVP
  or DoPČ paid irregularly was registered as ZECD1 / ZECD2 — the codes for
  regular monthly income. ZECD1N and ZECD2N were declared in the selection and
  reachable only by hand. The Sociálna poisťovňa treats the two as different
  relationships, so the employee was given the wrong insurance scope from the
  day of registration rather than on a single payslip. Backported from 19.0,
  reading ``l10n_sk_income_regular`` from ``hr.contract``.

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Clean copy — the report renders from user-entered
  registration events (not payslips or contract lifecycle), so no code or test
  change was required beyond the manifest version bump.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Slovak RLFO / RLZEC employee registration batch with
  prihláška (PA) and odhláška (OD) events built from the employee + hr.version
  lifecycle, validated against the official ``RLZEC-v2026.xsd``.
* ``typZec`` defaulted from the employee agreement type; odhláška branch
  (zecPPOdhl / zecNPOdhl / zecDOdhl) selected accordingly.
