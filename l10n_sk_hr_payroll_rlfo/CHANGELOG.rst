=========
Changelog
=========

18.0.1.2.0 (2026-11-05)
=======================

* **Added: RLZEC 2027.** The Sociálna poisťovňa's ``RLZEC-v2027.xsd``
  (published 2026-11-05) is shipped and pinned in ``SCHEMA_VERSION``, which
  this branch gains. A batch for January 2027 or later is generated in the 2027
  namespace and validated against it; earlier periods keep RLZEC 2026. 18.0's
  declaration base picks a version from today's date only, so the model
  resolves the period's version itself. Contributed by votrelec
  (cssk-public#16); port of 19.0.1.3.0.
* **Slovak catalogue** for the new fields and messages, and for the correction
  fields every declaration shares, which were still English.

18.0.1.1.1 (2026-11-05)
=======================

* **Fixed: statutory owners were registered as ordinary employees.** Every
  registration declared ``zamSUcastou`` false, so a statutory body or member
  with at least 50 % of the employer's property (§ 231 ods. 1 písm. o)
  z. 461/2003) was reported wrongly, and the XML still validated. Each
  registration event now records a reviewed status and its evidence; an
  unreviewed status or missing evidence stops generation, and both are locked
  once the batch is generated. Existing events start as *Not reviewed*.
  Contributed by votrelec (cssk-public#14); port of 19.0.1.2.3.

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
