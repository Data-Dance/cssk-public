======================
CZ VAT Return (DPHDP3)
======================

The Czech country layer for the shared VAT-return framework
(``l10n_cssk_vat_return_base``). It produces the Czech **VAT return** (přiznání
k DPH / DPHDP3) and is **CE-clean** — it computes from the core ``l10n_cz`` tax
tags and does **not** depend on the Enterprise ``account_reports`` engine, so it
runs on both Community and Enterprise.

The DPHDP3 line set is mapped to the ``l10n_cz`` tax tags (``VAT n Base`` /
``VAT n Tax``); the 48 tag-based lines auto-compute from the posted move-line
tags. Export is the EPO **Pisemnost / DPHDP3** XML (VetaD / VetaP / Veta1–Veta6),
following the structure the EPO portal accepts.

Features
========

* DPHDP3 line set (obrat23/dan23/…) mapped to the ``l10n_cz`` tax tags; the
  48 base/tax lines auto-compute from the move-line tags.
* EPO **Pisemnost / DPHDP3** XML export (VetaD / VetaP / Veta1–Veta6).
* CE-clean: reads tax tags directly, no ``account_reports`` dependency.

Usage
=====

*Accounting ▸ Reporting ▸ Czech Republic ▸ Přiznání k DPH.* Create a return for
a period, **Compute** to populate the tag-based lines from the period's postings,
review the lines, then **Export XML** for the EPO portal.

**Scope:** the base/tax lines compute from the tax tags; ř. 46 and the
totals ř. 62 – 66 compute from them as the EPO structure defines them (an
override on any of them is kept); the deduction-claim lines of the krácení
coefficient and ř. 60 are entered by the accountant. The export is validated
against the official EPO ``dphdp3_epo2.xsd``, pinned in
``data/SCHEMA_VERSION``.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
