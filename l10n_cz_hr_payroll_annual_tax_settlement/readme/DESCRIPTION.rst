Annual Czech **Vyúčtování daně z příjmů ze závislé činnosti** (DPZVD6) — the
income-tax reconciliation filed electronically to the Finanční správa (via EPO)
by 20 March of the following year.

The module aggregates the **whole calendar year** of payslips through the
engine-neutral ``l10n_cssk_payroll_declaration_base`` adapter and produces the
EPO ``<Pisemnost>`` / ``<DPZVD6>`` XML (no namespace), validated against the
shipped ``dpzvd6_epo2.xsd``.

Field mapping
-------------
* ``VetaD/@kc_dpzii01`` (Part II, row 1) ← Σ annual advance income tax
  (``INCOMETAX``).
* ``VetaD/@poc_zam1..12`` ← number of employees with a payslip in each month.
* ``VetaO`` (Part I, per month) ``@kc_dpzi01`` / ``@kc_dpzi02`` ← that month's
  advance income tax.
* ``VetaP`` ← payer identification: ``typ_ds`` (company subject type), ``dic``
  (DIČ), name / city / ZIP; ``VetaD/@c_ufo_cil`` ← company tax-office code.

Engine-neutral: reads payslips through the shared base adapter and works on both
the ``payroll`` engine and the ``hr_payroll`` engine.

Human-verify / assumptions
--------------------------
* Only the **advance tax** (záloha na daň, § 6) is reported. ``WHTAX`` (srážková
  daň zvláštní sazbou) belongs to a separate form (Vyúčtování daně vybírané
  srážkou) and is deliberately **not** included here to avoid double counting.
* Part II is filled on row 1 (Σ advances) only; the reconciliation
  difference / overpayment rows and the non-resident per-employee annexes
  (VetaC / VetaH) are left for manual completion.
* ``VetaD/@vdadpz_typ`` is fixed to ``B`` (řádné / regular); corrective and
  supplementary types are not modelled.
