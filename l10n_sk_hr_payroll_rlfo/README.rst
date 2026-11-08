=============================================
Slovakia — RLFO natural-person registration
=============================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Slovak social-insurance registration of employees (RLFO / RLZEC) filed to the Sociálna poisťovňa — registration / de-registration events built from the employee + hr.contract lifecycle, XML validated against RLZEC-v2026.xsd.**

Slovak **RLFO** (Registračný list fyzickej osoby) — the social-insurance
registration of employees filed to the Sociálna poisťovňa. It produces the
modern employee-only *hromadný* batch (root ``spRegListZec``, ns
``http://socpoist.sk/xsd/rlzec2026``) validated against the shipped
``RLZEC-v2026.xsd``.

Unlike the monthly/annual contribution statements this report is **not**
payslip-derived: its data comes from the employee and the ``hr.contract``
lifecycle. Each RLFO record holds a batch of registration **events**, one per
employee:

* **Prihláška (PA)** — registration, carrying the insurance start date
  (``datVznikPoist``);
* **Odhláška (OD)** — de-registration, carrying the insurance start + end dates
  (``zanik``).

The ``typZec`` relationship code defaults from the employee's agreement type
(employment → ``ZEC``, DoVP → ``ZECD1``, DoPČ → ``ZECD2``) and selects the right
odhláška branch (``zecPPOdhl`` / ``zecNPOdhl`` / ``zecDOdhl``). The birth number
(``rc``) is read from the employee's Identification No., the name is split into
surname/first name and the birth date from the employee — review these against
your master data before filing.

Change (``ZM``), interruption (``PE``) and cancellation (``ZP``) events are not
modelled yet.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_rlfo``
- **Version:** 18.0.1.2.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_cssk_payroll_declaration_base``

Authors: Data Dance s.r.o.
