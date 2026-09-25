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

**Scope note (v1):** the 48 base/tax lines auto-compute; the deduction-claim
lines (krácení coefficient) and the totals are entered/reviewed by the accountant
(manual) — the inter-line totals can be auto-wired after accountant validation.
The official EPO XSD is not yet wired (the export validates the root element and
is well-formed); add it for submission-grade validation.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
