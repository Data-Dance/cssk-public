=================================================
CZ Control Statement (Kontrolní hlášení / DPHKH1)
=================================================

The Czech country layer for the shared control-statement framework
(``l10n_cssk_kv_kh_base``). A line-level resolver classifies posted move lines
into the Kontrolní hlášení (DPHKH1) sections and the module exports the official
EPO Pisemnost / DPHKH1 XML. This is the **Czech** Kontrolní hlášení (KH) — not
to be confused with the Slovak Kontrolný výkaz DPH.

Features
========

* A line-level resolver classifies posted move lines into the KH sections.
* The per-document 10 000 CZK threshold splits the detail sections (A4/B2, over)
  from the aggregates (A5/B3, up to).
* Reverse-charge supplies and acquisitions (§92a) are routed to A1/B1; EU
  acquisitions (pořízení zboží z jiného členského státu) to A2.
* Exports the EPO Pisemnost / DPHKH1 XML: VetaD/VetaP, the per-document
  VetaA1/A2/A4/B1/B2 rows, the VetaA5/B3 aggregates, and the VetaC control
  totals computed from the sections.

Usage
=====

Install the module on a Czech company. Create a control statement for the
reporting period; computing the lines populates the A1–B3 sections from the
posted move lines, applying the 10 000 CZK per-document split between the detail
and aggregate sections. Export the statement to produce the EPO Pisemnost /
DPHKH1 XML for submission.

Scope note (v1): the resolver decision tree — especially the §92a reverse-charge
commodity list and the §44 bad-debt corrections (oprava výše daně u pohledávek
za dlužníky v insolvenci) — needs CZ-accountant validation. The export is
validated against the official EPO **DPHKH1** XSD (``data/dphkh1_epo2.xsd``),
loaded onto the statement version record.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
