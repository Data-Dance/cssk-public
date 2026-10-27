=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Employer premium rounded on the company total.** The employer's 24.8 %
  is now worked out on the sum of all employees' assessment bases and rounded
  up once (§ 7 odst. 1 písm. a) and odst. 3 zák. 589/1992 Sb.); before, the
  payslip premiums were summed and rounded half-up, which could report a crown
  less than is owed. Each employee's own premium is rounded up separately.
- **The assessment base is reported, not reconstructed.** *zakladZamestnavateleA*
  was the employer premium divided by 24.8 %; it is now the sum of the
  employees' monthly bases (§ 5a odst. 1 písm. a)), each rounded up to whole
  crowns (§ 5d), taken from the social-insurance line of the payslip — capped
  at the annual maximum, and absent for an uninsured month.
- **Employer discount on the total of the bases.** The § 7a discount is 5 %
  of the discounted employees' bases together, rounded up (§ 7b odst. 1), and
  the annex reports each employee's assessment base rather than the gross.
- Draft payslips are no longer counted, and payslips crossing the month end
  are reported in the month they end in (see the declaration base).

[19.0.1.1.2] — 2026-10-27
-------------------------

Changed
~~~~~~~

- **PVPOJ follows the JMHZ transition.** From January 2026 the premium is
  reported in the unified monthly employer report (JMHZ, Act No. 323/2025
  Coll.); the ČSSZ took PVPOJ for the last time for December 2025. The one
  exception, Act No. 360/2025 Coll., Art. IX point 3 — an employer that is
  no longer an employer on 1 April 2026 files PVPOJ for January to March
  2026 — is still generated; for any other company those months are
  refused, and April 2026 onwards always is.
- **A month before 2025 is refused** instead of being rendered in the 2025
  structure, the only one shipped: the form version now follows the period.
- The discount annex splits the employee's name like ELDP and ONZ: the last
  word is the surname (it used to be everything after the first word).

19.0.1.1.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

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
