=========
Changelog
=========

18.0.1.5.1 (2026-11-09)
=======================

Back-ported from 19.0: every change below, as released there.

18.0 differences: the employment periods and the contract on a given day come
from the employee's running and expired ``hr.contract`` records (drafts and
cancelled contracts are not employment); Enterprise payslips count as
confirmed in ``done`` and ``paid`` (19.0: ``validated``).

Unreleased
==========

Added
~~~~~

- ``SEPARATE_TAX_BASE`` in the Czech rule-code map: ``PAR6BASE`` on both
  engines, the separate tax base of § 6 odst. 4 ZDP from 2027.

- ``_payslip_version(payslip)``: the contract version a payslip was computed
  on, engine-neutral (Enterprise ``version_id``, OCA ``contract_id``), falling
  back to the version in force on its end date. Declarations that classify a
  payslip by its contract use it instead of the employee's current version,
  which a later edit of the employee card would change (cssk-public#12).

Fixed
~~~~~

- **A form filed separately to several recipients can scope its amendments
  to the recipient.** The check that a corrective filing has something to
  amend matched company and period only; a form now names the fields that
  identify the original (``_amendment_scope_fields``), such as the health
  insurer of a per-insurer overview.

[19.0.1.5.0] — 2026-10-27
=========================

Fixed
~~~~~

- **Draft and waiting payslips are no longer declared.** Every declaration
  counted any payslip that was not cancelled, so a draft someone was still
  working on — or had abandoned — reached the authority. Only confirmed
  payroll is reported now: *Done* on the OCA engine, *Validated* or *Paid* on
  Enterprise. Confirm the month's payslips before generating.
- **Payslips that cross a month or year boundary were dropped.** A payslip
  was taken only if it lay entirely inside the period, so one for 15 March
  – 14 April, or a December payslip ending in January, appeared in no
  declaration at all. A payslip now belongs to the period its end date falls
  in, so each one is reported exactly once.
- **Insured days follow the employment, not the length of the period.**
  The per-employee days were always the whole month (or year); they are now
  the days of employment inside the period, read from every contract version
  of the employee rather than only the current one.
- **The version picker offers only the form being prepared.** It listed the
  vintages of every form of the country.

Added
~~~~~

- A *Payroll Reporting* tab on the company form with the ČSSZ variable
  symbol and OSSZ code; the declarations refused to generate without them but
  there was nowhere to enter them.
- The payslip adapter also returns each rule's base (amount × quantity), so a
  form can report an assessment base instead of deriving it from a premium.

[19.0.1.4.4] — 2026-10-27
=========================

Fixed
~~~~~

- **The form version now follows the period, not today.** A declaration
  picked its form version from the day it was created, so last year's filing
  prepared this year was rendered in this year's vintage. *Generate* now
  switches to the version valid for the period, and refuses a period no
  version covers — including a period after a form was discontinued — with a
  message naming the form and, where the form module knows it, what replaced
  it. *Version* is no longer a required field for that reason: its default
  comes from today and may legitimately be empty.
- **A correction of an annual filing prepared in a later month was refused.**
  The check for an earlier submitted filing compared the year *and the
  month*, and an annual form keeps the month it was created in. It now
  compares the period (first and last day), so an annual corrective filing
  finds the regular one whatever month either was created in.

Added
~~~~~

- A shared helper that splits an employee's name into first name and surname
  for the authority forms (the last word is the surname; separate first/last
  name fields are used when a module provides them).

19.0.1.4.1 — 2026-09-13
=========================

Fixed
~~~~~

- **The chatter posted its own HTML as visible text.** ``message_post``
  ESCAPES a plain ``str`` and renders only a ``markupsafe.Markup`` —
  ``mail_thread.py`` states it on the parameter and applies it at
  ``'body': escape(body)``. Nothing failed: the post succeeded and the log was
  clean, which is why it survived to a user.
- Built as ``Markup(template) % args`` rather than by wrapping the finished
  string. ``%`` on a ``Markup`` escapes what it substitutes; wrapping the join
  renders it — and the interpolated values here are not ours, so the shorter
  fix would have turned an escaping bug into an injection one.

- One site: the "Marked **submitted**" note. A translated
  string carrying ``<b>`` — the same defect in a shape a search for
  ``"".join`` cannot see.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added Czech (``i18n/cs.po``) and Slovak (``i18n/sk.po``)
  translations of the declaration/period/state-machine/XSD terminology.

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. The declarative ``models.Constraint`` (19.0) on the
  per-employee annex is expressed via ``_sql_constraints`` for 18.0. The
  engine-neutral payslip adapter (``_collect_payslip_totals``) is unchanged.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release.
* ``cssk.payroll.declaration.mixin`` — engine-neutral declaration sheet with a
  ``draft → generated → submitted`` state machine and an XSD-validated XML
  export pipeline.
* ``cssk.payroll.employee.declaration`` — per-employee annex source.
* ``cssk.payroll.declaration.version`` — form-vintage record carrying the QWeb
  template, root element and the shipped XSD.
* ``_collect_payslip_totals`` payslip adapter reading the common ``hr.payslip``
  API shared by the ``payroll`` and the ``hr_payroll`` engines
  (no dependency on either).
