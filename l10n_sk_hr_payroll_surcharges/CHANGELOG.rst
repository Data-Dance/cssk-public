=========
Changelog
=========

Unreleased
==========

Changed
~~~~~~~

- **Renamed from ``l10n_sk_hr_payroll_priplatky``.** The technical name is
  now English, like most of the repository. No migration is shipped, because
  the module was not yet installed in production. A development database
  that had it installed keeps an orphaned ``l10n_sk_hr_payroll_priplatky``
  row. Install ``l10n_sk_hr_payroll_surcharges`` there.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 6f9cc41 on branch 18.0-catch-up (reaches 18.0
  when that branch lands) — do not port this again.
  **The rename (2026-09-30), not yet on 18.0.** 18.0 still ships
  ``l10n_sk_hr_payroll_priplatky``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

Carry-over to 20.0
~~~~~~~~~~~~~~~~~~

- DISCHARGED 2026-09-30 by 51a5085 on branch 20.0 — do not port this again.
  **The rename (2026-09-30), not yet on 20.0.** 20.0 still ships
  ``l10n_sk_hr_payroll_priplatky``. Rename it together with the rest of the
  2026-09-30 batch (the fiscal-year closing, surcharges, annual tax
  settlement and inventory verification modules). Rename every reference
  too: dependent manifests, ``odoo.addons.*`` imports, the ``.pot`` file
  name and ``module_*`` settings toggles. The 19.0 commit is the checklist.

19.0.1.2.2 — 2026-09-13
=========================

Fixed
~~~~~

- **A field label was being INVENTED, not missing.** ``fields.Float("Night
  work %", ...)`` passes ``string`` positionally, and
  ``tools/i18n_export_offline.py`` read it from keyword arguments only — so it
  fell back to deriving a label from the field name and wrote "Noc Pct" into
  the catalogue where Odoo's own export writes "Night work %". Every
  translation keyed to the derived form was therefore keyed to a msgid the
  runtime never looks up: present, valid, and dead.
- The exporter now reads the positional slot, which differs per field type
  (``Many2one`` puts ``comodel_name`` first, ``One2many`` two arguments,
  ``Many2many`` four, ``Selection`` its selection). Positional ``selection``
  lists are extracted too, which is where the stupne-náročnosti and VRP2
  receipt-state labels had been going missing entirely.
- Catalogues regenerated against the corrected msgids and re-translated.

19.0.1.2.1 — 2026-09-13
=========================

Added
~~~~~

- **Slovak catalogue — the module had none.** Generated with
  ``tools/i18n_export_offline.py`` (no database is available here) and verified
  back through Odoo's own ``PoFileReader``, so every entry resolves to the
  record it belongs to rather than importing as code strings only.

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.2.0 (2026-08-05)
=======================

* The §85 ods. 5 ustanovený týždenný pracovný čas moved from the
  ``STANDARD_WEEKLY_HOURS`` literal onto the dated wage-surcharge rate record
  as ``standard_weekly_hours``. It still defaults to 40 inside the Odoo-free
  kernel so that stays callable standalone, but the Odoo layer now passes the
  dated value: a statutory change is a data change.

19.0.1.0.1 (2026-08-03)
=======================

* **Fix a silent overpayment in the minimum-wage top-up.** The ordinary hours
  driving the comparison were taken from the ``WORK100`` worked-day line, but
  the two engines disagree about what that line holds: the OCA engine returns
  the FULL days the calendar schedules and states outright that it "don't
  substract leaves by default", while Enterprise groups real work entries by
  type so absences never land there. On the OCA engine an employee absent for
  a whole month therefore had their basic wage prorated to zero while still
  showing a full month of hours, and was paid the entire monthly minimum wage
  as a "top-up". The hours are now netted against the absence lines, with the
  engine difference isolated behind ``_l10n_sk_work100_is_gross`` and
  overridden in the OCA bridge. Regression tests on both engines.
* The scheduled-hours fallback now triggers on the ABSENCE of worked-day lines
  rather than on the hours summing to zero. A full month of leave legitimately
  yields zero hours, and the old test resurrected the same overpayment.
* ``surcharge_pct`` raises on an unknown code or a missing base percentage
  instead of returning 0 %. Every figure it returns is a statutory minimum, so
  a rate record that predates a newly added surcharge code would otherwise pay
  nothing at all, silently and unlawfully.
* Both defects were found by an independent review from a different model
  family (gpt-5.3-codex), not by the test suite.

19.0.1.0.0 (2026-08-03)
=======================

* Initial release.
* ``l10n.sk.wage.surcharge.rate`` — dated statutory percentages for the night,
  Saturday, Sunday, public-holiday, overtime, difficult-conditions and standby
  surcharges, including the risky-work variants and the lower rates a
  collective agreement may set.
* ``l10n.sk.minimum.wage`` — the six stupne náročnosti minimum wage claims
  (§ 120), monthly and hourly, for 2024, 2025 and 2026. The level-1 hourly
  figure doubles as the base of the surcharges that are percentages of the
  minimum hourly wage.
* ``surcharge_calc`` — the arithmetic, deliberately free of Odoo imports so it
  can be unit tested on its own. Amounts round UP to the cent: every figure in
  the Zákonník práce is a statutory floor, so a half-up rounding that went
  down would underpay.
* ``sk.surcharge.payslip.mixin`` — engine-neutral payslip half, taking the
  hours from a worked-days line where the work-entry stack supplies one and
  from a payslip input otherwise.
* The minimum-wage top-up measures monthly-paid and hourly-paid employees
  against different figures, because the two statutory minima genuinely
  disagree: the published hourly amounts are the monthly amount over the
  statutory 174 hours, so in a month scheduling more (June 2026 schedules
  176) an employee on exactly the monthly minimum falls short of the hourly
  one while owing nothing. Salaried contracts are therefore compared against
  the monthly claim, prorated per § 120 ods. 4 by hours worked over the hours
  a FULL-TIME contract would have worked — not over the employee's own
  schedule, which would always give a ratio of 1 and hold a part-timer to the
  undiminished minimum.
* Every surcharge, the overtime pay and the wage replacements are excluded
  from that comparison per § 120 ods. 3, so a night-shift surcharge cannot
  paper over a sub-minimum base wage.
* Installing this module changes existing payslips wherever a contract pays
  below the statutory minimum — that is the point of it, but it is a visible
  change. Two fixtures in ``l10n_sk_hr_payroll_oca`` and
  ``l10n_sk_hr_payroll_ee`` used a €500 full-time wage to exercise the health
  OOP; a full-time contract at that wage is unlawful in Slovakia, so they were
  changed to half-time contracts, which keeps the same €500 gross and the
  same OOP arithmetic.

19.0.1.1.0 (2026-08-03)
=======================

* ``hr.job.l10n_sk_wage_level`` — the § 120 difficulty level now lives on the
  POST, which is what Annex 1 to the Zákonník práce actually classifies, and
  contracts inherit it. Recording it only per contract meant re-deciding it at
  every hire and letting two people on the same job drift apart.
* **``l10n_sk_wage_level`` no longer defaults to "1".** The default was
  indistinguishable from a deliberate classification as pomocné práce, and it
  silently made the job inheritance dead code — the field was never empty for
  it to fill. Everything downstream reads the level as ``level or "1"``, so an
  unclassified post still behaves as the plain minimum wage; it simply no
  longer claims to have been classified.
* ``l10n_sk_min_wage_warning`` — a contract-level warning when the agreed wage
  falls below the claim for its level. The payslip top-up quietly corrects
  such a wage every month, which is the right thing to PAY but lets an
  unlawful contract sit in the system unnoticed. Prorated per § 120 ods. 4, so
  a part-timer on a proportionate wage is not warned; skipped for dohody
  (outside § 120) and for hourly contracts (compared per hour on the payslip).

19.0.1.1.1 (2026-08-03)
=======================

* **Fix: no minimum-wage top-up for a dohodár.** § 120 sets minimum wage
  claims for a pracovný pomer. A worker on an agreement is entitled to the
  minimum HOURLY wage under zák. 663/2007 instead and has no stupeň
  náročnosti, so topping their monthly remuneration up to a full-time monthly
  claim invented an entitlement they do not have — a dohodár on €400 was being
  paid up to €915. The contract-level warning added in 19.0.1.1.0 already
  skipped agreements; the payslip rule did not.

19.0.1.1.2 (2026-08-03)
=======================

* Salary rules now ask the applicability table in
  ``l10n_sk_hr_payroll_base`` which contributions and entitlements
  apply to this employment form, instead of each re-deriving it from
  the agreement type. The rule states the question
  (``l10n_sk_applies('SICKNESS_INSURANCE')``) and the answer lives in
  one readable table.

[19.0.1.2.4] — 2026-09-13
=========================

Fixed
~~~~~

- **Code translations that Odoo was never loading.** An entry whose references
  are ``code:addons/...`` is treated as a Python translation only if it carries
  the extracted comment ``#. odoo-python`` — ``_load_python_translations``
  filters on exactly that and never on the reference. Without it an entry can
  name the right ``.py``, carry a correct msgstr, pass ``msgfmt --check``, and
  be silently ignored for ever. This module's hand-added entries were in that
  state. Repaired by ``tools/fix_po_code_comments.py``, which is also the CI
  check; the offline exporter now emits the comment itself.

