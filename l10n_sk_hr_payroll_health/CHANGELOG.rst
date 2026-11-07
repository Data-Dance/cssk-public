=========
Changelog
=========

Unreleased
~~~~~~~~~~

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.2.3] — 2026-11-07
-------------------------

Fixed
~~~~~

- **Pensioners and foreign-insured workers on DoVP/DoPČ are left out of the
  dávka 514.** § 10b ods. 1 písm. a) z. 580/2004 excludes agreement income of
  every pensioner group *Pension granted (SK)* offers; the contract the payslip
  was computed on decides, not the employee's current one. A health-exempt
  agreement without a pension (e.g. an A1 worker) is left out too, so the
  payslip (no advances) and the statement (no row) agree. Contributed by
  votrelec (cssk-public #15).
- Generation stops when a DoVP/DoPČ has a pension but is not marked
  health-exempt, since its payslip then carries advances the statute excludes.
  Only the insurer the statement is addressed to is checked.

18.0 carry-over: not ported. 18.0's ``hr.contract`` has no pension type; the
health-exempt half applies there and is still to do.

[19.0.1.2.2] — 2026-11-05
-------------------------

Fixed
~~~~~

- Czech catalogue: translated the strings that were still English.

[19.0.1.2.1] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **The company's default health insurer is on the company form** (tab
  *Payroll Reporting*, together with the *Health payer number*). It decides
  the dávka 514 of every employee without an insurer of their own, and could
  be changed only by import.
- A correction of a dávka 514, once offered, will look only for the statement
  sent to the same insurer.

**Changed**

- **Slovak translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now, as is the message asking for the company DIČ.

[19.0.1.2.0] — 2026-10-27
~~~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- **Each insurer's dávka 514 lists only its own insurees.** Every employee with a payslip went into the dávka of whichever insurer the record was addressed to, so a company with employees at two insurers reported everybody to both. Employees now carry a *Health insurer (SK)* on their form; an employee without one counts as insured with the company's default insurer.

**Added**

- The *Health payer number* can be filled in on the dávka 514 form. Generation requires it, but it was on no form anywhere.
- ``data/SCHEMA_VERSION`` pins the bundled ``514-2023.xsd``, with a test that the bytes still match.


19.0.1.1.0 (2026-09-16)
~~~~~~~~~~~~~~~~~~~~~~~

* **The dávka 514 no longer files without a DIČ.** ``_preflight`` checked the
  IČO, the health payer number and the target insurer, but not the DIČ, while
  ``_declaration_render_context`` read it as
  ``self._digits(getattr(company, "l10n_sk_dic", ""))[:12]`` — a ``getattr``
  default and a ``_digits`` that turns a missing value into ``""``. So a company
  with no DIČ produced an empty ``<CompanyIDTaxCode>`` and the dávka went to the
  health insurer with nothing in it, no error raised and no warning logged. The
  Prehľad and the Hlásenie have always refused in that situation; this one did
  not. It now refuses too, with the same message.

* Depends on ``l10n_sk_base``, which owns the DIČ field this module reads.

19.0.1.0.1 (2026-07-06)
~~~~~~~~~~~~~~~~~~~~~~~

* Normalized all user-facing strings to clean English (removed mixed-language
  parentheticals). Added a Slovak (``i18n/sk.po``) translation and the
  extraction template (``i18n/<module>.pot``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: monthly SK dávka 514 (Mesačný výkaz preddavkov na poistné)
  for VšZP / Dôvera / Union — root ``MZSR`` following the official
  ``514-2023.xsd`` element model: Identification + CorporateBody + InsuranceBody
  aggregate + one PersonData row per employee. Insurer code (25/24/27) is
  company config / a per-declaration selection.
* Rule mapping DepositOfEmployer↔HEALTHEMPLOYER, DepositOfEmployee↔HEALTH,
  DepositOffEmployeeAdd↔HEALTHDOPLATOK / HEALTH_DOPLATOK.
* Ships and loads the official ``514-2023.xsd``, but runs it as a non-fatal
  check: the published schema is internally defective (single-char ``[0-9]``
  patterns under multi-char minLength, impossible integer bounds) so no real
  instance can pass ``assertValid``; the authoritative gate is well-formedness
  + structural conformance to its element model.

19.0.1.0.2 (2026-08-03)
~~~~~~~~~~~~~~~~~~~~~~~

* Read the engine-dependent salary-rule codes from
  ``l10n_cssk_payroll_declaration_base.rule_codes`` instead of restating
  them locally. No behaviour change; the local tuples were correct, but
  the knowledge now has one home rather than three.
