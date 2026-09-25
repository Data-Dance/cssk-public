Annual Czech **ELDP** (Evidenční list důchodového pojištění) — the per-employee
pension-insurance record filed to the ČSSZ (annually by 30 April, and within 30
days of an employment ending).

For each employee the module aggregates the **whole calendar year** of payslips
through the engine-neutral ``l10n_cssk_payroll_declaration_base`` adapter and
produces one ``<eldp09>`` record inside the batch ``<RELDP>`` envelope (ns
``http://schemas.cssz.cz/ELDP09``), validated against the shipped ``ELDP09.xsd``.

Field mapping
-------------
* ``items/t1/@inc`` (vyměřovací základ / assessment base) ← Σ ``GROSS`` for the
  year.
* ``items/t1/@din`` (days) ← employment period (``contract_date_start`` ..
  ``contract_date_end``) intersected with the reporting year.
* ``eldp09/@typ`` ← ``1`` if the employment continues past year-end, ``2`` if it
  ended during the year.
* ``client`` ← employee name / birthday / birth number (Identification No.) /
  private address; ``comp`` ← employer name / IČ / ČSSZ variable symbol.

Engine-neutral: reads payslips through the shared base adapter and works on both
the ``payroll`` engine and the ``hr_payroll`` engine.

Human-verify / assumptions
--------------------------
* The pension assessment base is taken as the **uncapped** annual gross
  (Σ ``GROSS``); the statutory maximum assessment base ceiling and any
  non-insurable income are **not** applied — verify for high earners.
* A **single continuous** insurance period per employee is emitted (one ``t1``);
  multiple engagements / interruptions within the year are not split.
* Excluded-day and deducted-day columns (``dex`` / ``dar``, and the ``m1..m13``
  month markers) are emitted empty / ``0`` — sickness/excluded periods are not
  yet derived from work entries.
* ``eldp09/@typ`` and the OSSZ code placement (``tco`` / ``dep``) should be
  reviewed against the current ČSSZ form logic before live filing.
