================================================
Czech Republic — ONZ (Employment Registration)
================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Czech employment registration (ONZ) for the ČSSZ — per-employee start/end events built from the employee and hr.contract lifecycle, XML validated against the official ONZ2022 XSD.**

Czech **ONZ** (Oznámení o nástupu do zaměstnání) — the ČSSZ employment
registration filed within 8 days of an employee's start or end of employment.

Unlike the aggregate/annual reports, ONZ is **event-driven** and built entirely
from the **employee + hr.contract lifecycle** (hire / termination dates, birth
number, name, address) — no payslip data is used. Each filing is a batch of
per-employee events (akce nástup / skončení), exported as the official XML (ns
``http://schemas.cssz.cz/ONZ2022``) and validated against the shipped
``ONZ2022_20230616.xsd`` (+ ``baseTypes2.xsd``).

Field mapping
-------------
* ``employee/@act`` ← ``1`` (nástup) or ``2`` (skončení), from ``event_type``.
* ``employee/@dep`` ← company OSSZ code; ``@dat`` ← today.
* ``client/name`` + ``client/birth`` + ``client/@bno`` ← employee name,
  birthday, birth number; ``client/fdr`` ← employee private CZ address.
* ``comp`` ← employer ČSSZ variable symbol / IČ / name.
* ``job/@fro`` ← contract start; ``job/@to`` ← contract end (skončení).

Human-verify / assumptions
--------------------------
* Only the two common akce codes (1 nástup / 2 skončení) are modelled; correction
  / cancellation actions and the many optional blocks (foreign insurer, pension,
  health-insurer change, unemployment-compensation data) are not generated.
* ``job/@rel`` is fixed to ``1`` (standard employment); other activity kinds
  (agreements, small-scope employment) are not distinguished.
* The birth surname (``birth/@nam``) is approximated by the current surname, and
  a missing house number (``fdr/@num``) is split off the private-street string —
  review before live filing.

.. rubric:: Module facts

- **Technical name:** ``l10n_cz_hr_payroll_onz``
- **Version:** 18.0.1.0.1
- **Licence:** AGPL-3
- **Requires:** ``l10n_cssk_payroll_declaration_base``

Authors: Data Dance s.r.o.
