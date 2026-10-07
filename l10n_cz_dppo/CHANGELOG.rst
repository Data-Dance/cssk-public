=========
Changelog
=========

All notable changes to **l10n_cz_dppo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.3.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **DPPDP9** ``VetaD`` now carries ``c_nace``, the company's CZ-NACE code, which
  EPO checks critically against the code list.

[19.0.1.2.0] — 2026-09-28
-------------------------

Fixed
~~~~~

- **Every DPPDP9 declared itself a return on entering liquidation.** VetaD
  carried ``typ_dapdpp="B"`` hard-coded, which the XSD defines as *daňové
  přiznání při vstupu do likvidace*; the ordinary return for the tax period
  is **A**. It is now a choice on the return (*Typ daňového přiznání*, the
  XSD's full code list), defaulting to A.
- **``typ_zo`` was "1", which is no letter of § 21a ZDP.** It is now derived
  from the period — a calendar year A, another twelve-month year B, anything
  longer D — and can be set by hand (C for the period from a merger's decisive
  day). ``typ_popldpp`` is a choice too, defaulting to 1 (ostatní).
- **"Dodatečné" exported E, which the form reads as "dodatečné-opravné".** D
  now exists and E is labelled for what it is (migration 19.0.1.2.0); a
  dodatečné return needs *Důvody zjištěny dne* (``d_zjist``) before export.
  Returns already exported are not touched.

TODO
~~~~

- CZ asset ř.50/150 wiring is still pending. The asset book-vs-tax difference is not yet fed
  into the DPPDP9 spine (připočitatelné ř.50 / odčitatelné ř.150); the SK counterpart
  (``l10n_sk_dppo``) is wired via the ``asset_diff`` line kind, CZ is not.

[19.0.1.1.0] — 2026-09-28
-------------------------

Added
~~~~~

- **Rozvaha and Výkaz zisku a ztráty inside the return.** The účetní závěrka
  is filed as the XSD's own výkaz records — VetaUA (aktiva: brutto / korekce /
  netto / netto minulé), VetaUD (pasiva) and VetaUB (VZZ druhové členění),
  zkrácený rozsah per vyhláška 500/2002 Sb., in thousands — with the VetaD
  header (``uv_vyhl``, ``uv_rozsah``, ``uv_mena``, ``uz_rad``, ``d_uv``). The
  figures are those of the ``l10n_cz_fs`` Rozvaha / VZZ linked to the return
  (new dependency), matched row by statutory designation; there is no second
  account mapping. Linking is explicit, and a half-linked pair, a statement of
  another period or company, an uncomputed one, or one missing a row the
  výkaz reads is refused by name.
- The EPO row číselník for the three tables (the XSD does not carry it) is
  vendored as ``data/uv_radky_500.csv``. Every row of the zkrácený rozsah is
  mapped or declared not applicable with a reason (C.II.1., C.II.3., pasiva
  C.III., VZZ V.), and every other výkaz record of the XSD is declared not
  applicable by table; a test enforces both, and checks each EPO total
  against its statutory parts by signed weight per account of the l10n_cz
  chart.
- ``data/SCHEMA_VERSION`` pins the XSD and the číselník (size + md5) with the
  refresh procedure.

Changed
~~~~~~~

- ``data/dppdp9_epo2.xsd`` replaced by the published file (it differed only in
  the order of a pattern's alternatives), and ``verzePis`` raised from 05.01
  to the published structure version 05.01.01.
- A return exported with no statements linked says so in the chatter: the
  závěrka must then go as an E-příloha.
- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.1] — 2026-07-04
-------------------------

Changed
~~~~~~~

- Statutory rounding unified to HALF-UP (``statutory_round()``/``statutory_whole()``). (Wave 1)
- Multi-company ``ir.rule`` (``company_id in company_ids``) added. (Wave 1)

Fixed
~~~~~

- Removed ``typ_ds="P"`` from the DPPDP9 VetaP element — that attribute belongs to the DPH forms,
  not the income-tax return. (Wave 1)
- EPO Pisemnost/DPPDP9 XML: empty attributes now emitted as ``None`` (omitted) instead of ``""``
  (XSD-invalid). (Wave 1)

[2026-06-30] — Baseline & i18n
------------------------------

Added
~~~~~

- Czech corporate income-tax return (DPPDP9) on ``l10n_cssk_income_tax_base``: II. oddíl tax
  spine (ř.10 → ř.340) mapped to the EPO ``VetaO/@kc_ii*`` attributes.
- ř.10 (výsledek hospodaření před zdaněním) computed from the P&L (class 6 − class 5, excluding
  income-tax accounts 591–599); připočitatelné/odčitatelné adjustments, §34 deductions and slevy
  are accountant-entered and aggregate into the spine.
- EPO Pisemnost/DPPDP9 XML export validated against the bundled official XSD
  (``data/dppdp9_epo2.xsd``).
- cs_CZ jsonb translations (i18n sweep).
