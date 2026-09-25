=========
Changelog
=========

Unreleased
==========

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

19.0.1.4.0 (2026-08-07)
=======================

* Added the ``MEAL_EMPLOYER`` concept, and recorded in ``NOT_COMPARABLE`` that
  its SIGN cannot be compared across engines: OCA emits the employer meal
  contribution positive and Enterprise negative, each assembling NET to match.
  The magnitude agrees and the employee is paid the same. Anything that ever
  reads this line must take ``abs()``, or the two engines disagree by twice
  the amount.

19.0.1.3.0 (2026-08-06)
=======================

* **A shared correction concept for all twelve declaration forms.** Every CZ
  and SK payroll authority accepts amendments to a filing it has already
  received, and every one spells it differently — riadny / řádný, opravný,
  dodatočný / dodatečný, storno. The four CONCEPTS are named once on the mixin
  (``correction_type``, plus ``correction_reference`` and ``is_correction``)
  and the wire spelling is left to each form's template.
* A form declares what its authority accepts in ``_supported_correction_types``
  and the selection narrows to that, so a user cannot pick a type the receiving
  system will reject. The default is regular-only: a form that has not been
  checked against its authority's rules offers nothing rather than offering an
  amendment that will bounce.
* The generate preflight refuses an amendment with nothing to amend. Sending an
  opravný for a period never filed is a rejection at best and a duplicate at
  worst, and it is an easy mistake — the form looks exactly like the regular
  one. Only a SUBMITTED filing counts; a draft has not reached the authority.

19.0.1.2.0 (2026-08-06)
=======================

* Added ``BASIC``, ``HOLIDAY_NAHRADA`` and ``EMPLOYER_OBSTACLE``
  (``PREKAZKANAHRADA``) to the Czech section of the shared rule-code map, for
  the new ``l10n_cz_hr_payroll_parity`` harness.

19.0.1.1.0 (2026-08-05)
=======================

* Added the ``EMPLOYER_OBSTACLE`` concept (``PREKAZKA_NAHRADA`` on both
  engines) to the shared rule-code map.

19.0.1.0.1 (2026-07-06)
=======================

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added Czech (``i18n/cs.po``) and Slovak (``i18n/sk.po``)
  translations of the declaration/period/state-machine/XSD terminology.

19.0.1.0.0 (2026-07-05)
=======================

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

19.0.1.0.2 (2026-08-03)
=======================

* ``rule_codes`` — the single home for which salary-rule codes carry which
  concept on which engine. The declaration modules had each worked this out
  privately: ``l10n_sk_hr_payroll_prehlad`` and ``l10n_sk_hr_payroll_hlasenie``
  carried byte-identical copies of the income-tax tuple, ``l10n_sk_hr_payroll_health``
  its own for the health top-up. All three were correct, which is the problem —
  being correct by three independent acts of care is not a property the fourth
  module inherits. ``sum_concept`` for runtime use (sums both engines' codes,
  so the caller never detects the engine) and ``codes_for`` for the parity
  harness, which must assert one engine specifically.

[19.0.1.4.2] — 2026-09-13
=========================

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Slovak or Czech screen. The template and the catalogues now carry them,
  and the Slovak or Czech is written.

[19.0.1.4.3] — 2026-09-13
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

