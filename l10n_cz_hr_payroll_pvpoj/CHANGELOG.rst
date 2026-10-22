=========
Changelog
=========

18.0.1.1.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

18.0.1.1.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API (separate contract record
  instead of the 19.0 employee version).

19.0.1.1.0 (2026-07-05)
-----------------------

* Wire the §7a employer social-insurance discount annex now that the CZ rule set
  ships a ``SOCIAL_DISCOUNT`` line and the ``l10n_cz_social_discount_category``
  eligibility field. When any payslip in the period carries a discount the report
  emits the aggregate ``slevaZamestnavatele`` block (count / Σ assessment base /
  Σ discount) and the per-employee ``slevaZamestnanci`` annex (name, date of
  birth, assessment base, ``duvodSlevy`` reason letter a–g, shorter weekly
  working time), and reduces ``pojistneUhrada`` by the discount. When nobody
  qualifies the optional blocks are omitted and the output is unchanged. Works
  on both payroll engines via the engine-neutral payslip-line adapter.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly CZ PVPOJ (Přehled o výši pojistného) employer
  overview, aggregated from ``SOCIALERTOT`` / ``SOCIALEETOT`` and validated
  against the official ``PVPOJ25.xsd`` (+ ``baseTypes2.xsd``).
* The optional part-time premium-discount annex (``slevaZamestnanci``) is
  stubbed/omitted: that discount has no salary rule yet (documented TODO).
