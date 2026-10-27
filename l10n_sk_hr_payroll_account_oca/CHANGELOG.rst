=========
Changelog
=========

[19.0.1.0.3] — 2026-10-27
=========================

**Fixed**

- Loading the Slovak chart no longer fails for a user without payroll rights (an accounting manager or settings administrator setting up a new company). OCA payroll gives such a user no write access to salary rules, so mapping their accounts raised an access error and aborted the chart. The mapping now runs as superuser.

[19.0.1.0.2] — 2026-10-27
=========================

**Fixed**

- The *Annual Tax Settlement* line (342000), *Employer Work Obstacle Pay (§ 142)* (521000) and, when installed, the wage surcharges and the minimum-wage top-up (521000) now have accounts. They used to land in the journal's adjustment line. A test asserts that every rule carrying money has an account.

19.0.1.0.1 (2026-07-06)
=======================

* i18n pass: added ``i18n/<module>.pot`` and ``i18n/sk.po`` (module exposes no localizable source strings beyond inherited framework labels; Slovak GL account names remain in code comments only).

