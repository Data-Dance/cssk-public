=========
Changelog
=========

18.0.1.1.2 (2026-11-09)
=======================

Back-ported from 19.0: every change below, as released there.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.2] — 2026-11-07
-------------------------

Changed
~~~~~~~

- **The statement ends with the 2026 tax period.** Act No. 360/2025 Coll.
  abolishes the annual vyúčtování daně z příjmů ze závislé činnosti from the
  2027 tax period; the data are reported monthly in the JMHZ (Act No.
  323/2025 Coll.). The form version now closes on 31 December 2026, and a
  statement for 2027 or later is refused with a pointer to the JMHZ. A
  post-migration writes ``valid_to`` on the ``noupdate`` version record.

[19.0.1.1.1] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak catalogue: translated the strings that were still English.

[19.0.1.1.0] — 2026-10-27
-------------------------

Added
~~~~~

- **Příloha č. 1 — Počet zaměstnanců (VetaB).** Filed with every annual tax
  settlement (§ 38j odst. 1 ZDP) and missing until now: the employees on the
  payroll on 1 December, counted per municipality (ZÚJ) of their place of
  work. The place is the employee's work address; agreement workers (DPP /
  DPČ) and employees without a work address count at the employer's seat.
  Set *Municipality code (ZÚJ)* on the company and on every work address;
  generation stops and names the addresses that lack one.
- The company form shows the tax-office code, the filing subject type and the
  ZÚJ (tab *Payroll Reporting*).

Fixed
~~~~~

- Draft payslips are no longer counted, and a payslip is placed in the month
  it ends in, so a payslip crossing New Year lands in the right year.

[19.0.1.0.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The tax advances were reported before tax credits.** Part I columns 1 and
  2 and Part II row 1 took the payslip's tax before the basic taxpayer credit
  and the child tax benefit, overstating the tax for everyone with a signed
  declaration. They now report the advance after the monthly credits, as the
  form's instructions require.
- **Child tax bonuses were missing.** Part I column 5 (monthly bonuses paid)
  and Part II row 4 (their total) are now filled from the payslips.
- **Employee counts per month** now count the employees on the payroll on the
  last day of the month, as the form asks, instead of everyone who had a
  payslip in the month.
- The record's period is now the whole calendar year (1 January to
  31 December) whatever month it was created in.

Unreleased
----------

- **Renamed from ``l10n_cz_hr_payroll_vyuctovani``**, as on 19.0
  (2026-09-30). The technical name is now English, like most of the
  repository. No migration is shipped, because the module was not yet
  installed in production. A development database that had it installed
  keeps an orphaned ``l10n_cz_hr_payroll_vyuctovani`` row. Install
  ``l10n_cz_hr_payroll_annual_tax_settlement`` there.

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. Report logic unchanged; the runtime test's data
  setup was adapted to the 18.0 ``hr.contract`` API.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual CZ Vyúčtování daně ze závislé činnosti (DPZVD6) EPO
  reconciliation, aggregating advance income tax (``INCOMETAX``) over the
  calendar year — annual total in Part II, per-month rows in Part I — validated
  against the official ``dpzvd6_epo2.xsd``.
* WHTAX (srážková daň) excluded (separate form); Part II difference rows and
  non-resident annexes left for manual completion (documented human-verify
  notes).
