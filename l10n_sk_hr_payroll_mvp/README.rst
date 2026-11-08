===================================================
Slovakia — MVP monthly social-insurance statement
===================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Monthly Slovak social-insurance statement (MVP/MVPP) for the Sociálna poisťovňa — aggregate summary + per-employee annex, XML validated against MVPP-v2026.xsd. Engine-neutral (payroll or the hr_payroll engine).**

Monthly Slovak **MVP / MVPP** (Mesačný výkaz poistného a príspevkov) — the
social-insurance statement filed to the Sociálna poisťovňa each month.

It produces both the employer-aggregate summary (``poistne``, one amount pair
per fund) and the full per-employee annex
(``priloha/poistneZamestnancov/poistneZamestnanca``, one row per employee),
mapping the Slovak social rule codes 1:1 onto the fund structure (np↔SICK,
sp↔PENSION, ip↔DISABILITY, pvn↔UNEMPLOYMENT, up↔ACCIDENT, gp↔GUARANTEE,
rfs↔RESERVEFUND, pfp↔SHORTTIME). The exported XML (ns
``http://socpoist.sk/xsd/mvpp2026``) is validated against the shipped
``MVPP-v2026.xsd``.

Engine-neutral: it reads payslips through the shared
``l10n_cssk_payroll_declaration_base`` adapter and works on both the
``payroll`` engine and the ``hr_payroll`` engine.

The per-employee ``rc`` (rodné číslo) is read from the employee's
Identification No. field and the ``typZec`` relationship type defaults to a
regular employee (ZEC) — review both against your master data before filing.

.. rubric:: Module facts

- **Technical name:** ``l10n_sk_hr_payroll_mvp``
- **Version:** 18.0.1.1.0
- **Licence:** AGPL-3
- **Requires:** ``l10n_cssk_payroll_declaration_base``

Authors: Data Dance s.r.o.
