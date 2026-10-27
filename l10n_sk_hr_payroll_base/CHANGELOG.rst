=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.0] — 2026-10-27
-------------------------

**Fixed**

- The applicability table knows the worker's pension: § 4 ods. 1 písm. b) (no sickness or unemployment insurance on a DoVP/DoPČ with a dôchodok), § 19 ods. 3 písm. b) (no unemployment insurance after a starobný, predčasný starobný or over-70 % invalidný dôchodok) and § 128 ods. 3 (no disability premium after a starobný or predčasný starobný dôchodok, or a výsluhový one at pension age). The workaround of unticking *Regular monthly income* for a pensioner is no longer needed.
- The short-time work contribution applies to a pracovný pomer only (§ 128 ods. 1 písm. g) zákona 461/2003), not to a dohoda with a regular income.

[19.0.1.0.1] — 2026-10-27
-------------------------

**Fixed**

- A student on a **DoBPŠ** is no longer charged sickness or unemployment insurance (nor the short-time work contribution), even with a regular monthly income: § 4 ods. 1 písm. a) zákona 461/2003 takes the DoBPŠ out of the definition of a zamestnanec for those funds, and with a regular income the student is pension-insured only (§ 4 ods. 2 písm. b) bod 1). Applies to both payroll engines.
- Pensioners on a DoVP/DoPČ (§ 4 ods. 1 písm. b)) are still charged, because the contract records no pension status; untick *Regular monthly income* for them.
- The note on wage surcharges cites the paragraphs § 223 ods. 2 ZP actually extends to dohody (§§ 122a, 122b, 123; there is no § 122c).

19.0.1.0.0 (2026-08-03)
-----------------------

* Initial release.
* ``applicability`` — one table stating which contributions and entitlements
  apply to which of the four Slovak employment forms, and under which income
  regularity. Odoo-free, so it reads and diffs as the statement of law it is.
* ``hr.version.l10n_sk_applies(concept)`` — reachable from a salary-rule
  condition on either engine, since both hand the version to every rule.
* An unknown concept raises. Returning a default would let a typo look like a
  legal answer, and every caller is deciding whether to charge or pay someone.
