Czech **health-insurance** employer e-filings, built on the engine-neutral
``l10n_cssk_payroll_declaration_base``. Both employer filings that the health
insurers require are shipped together, since the same insurer expects both:

**PPPZ — Přehled o platbě pojistného zaměstnavatele** (monthly premium overview)
  Employer-aggregate, **no personal data**: the number of insured employees, the
  sum of their health assessment bases and the total 13.5 % premium. It is
  **payslip-derived** — the premium is summed from the ``HEALTHEE`` (employee
  4.5 % withholding) and ``HEALTHER`` (employer 9 %) rule codes and the
  assessment base is recovered as ``premium / 0.135`` (which makes the
  minimum-assessment-base top-up come out right). The XML (ns
  ``http://xmlns.vzp.cz/PrehledPlatbyZamestnavatele/v1``) is validated against
  the shipped ``PPPZ_2025_v8.xsd``.

**HOZ — Hromadné oznámení zaměstnavatele** (bulk employee notification)
  Event-driven per-employee **enrol (P) / terminate (O)** changes, built from the
  employee + ``hr.version`` lifecycle (hire / termination dates, birth number,
  name, private address) — **not** payslip totals. The XML (ns
  ``http://xmlns.vzp.cz/hromadneOznameniZamestnavatele/v1``) is validated against
  the shipped ``HOZ_2025_v8.xsd``.

Per-insurer filing
------------------
Czech health insurance uses **one common XML format** but is filed **per
insurer** through that insurer's own channel (VZP Point for VZP; the shared
"Portál zdravotních pojišťoven" for the rest). Seven insurers are supported as a
selection — VZP (111), VoZP (201), ČPZP (205), OZP (207), ZPŠ (209), ZPMV ČR
(211), RBP (213). Each employee belongs to one insurer
(``hr.employee.l10n_cz_health_insurer_code``, defaulting to the company's
``l10n_cz_health_insurer_code``); a PPPZ/HOZ sheet targets one insurer and only
that insurer's employees are aggregated/reported. Generate one sheet per insurer.

Engine-neutral: PPPZ reads payslips through the shared base adapter and works on
both the ``payroll`` engine and the ``hr_payroll`` engine.

**Assumptions / not implemented (see model docstrings):** HOZ covers the standard
resident-employee ``P``/``O`` codes only — the special ``kodZmeny`` codes
(EU/third-country first enrolment, state-payer facts, corrections) are out of
scope, and foreign-insured employees without a rodné číslo (the ``M``/``Z`` +
date-of-birth identifier) are not derived automatically. The employer payer
number (``identifikacniCisloPlatce``) defaults to ``<IČ>00`` (single accounting
office); set the ``Health payer number`` company field for a different office
sub-number.
