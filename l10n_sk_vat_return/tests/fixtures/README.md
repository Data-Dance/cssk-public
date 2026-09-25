# Filed Slovak VAT returns — a real oracle

`filed_vat_returns.json` holds **38 VAT returns that were actually submitted to
the Slovak tax office**, covering 2022-12 to 2025-12. Every figure in it was
filed; none was computed by this module or by the importer that extracted it.

That is the whole point. A localisation validated against constructed cases
proves that it agrees with whoever constructed them. This file lets it be
checked against what a real company really declared.

## Shape

    {
      "period":   "2025-07",        # the filing period
      "form":     "DPH2025",        # the FORM VINTAGE the return was filed on
      "kind":     "R",              # R = riadny, D = dodatočné
      "filed_on": "2025-08-18",
      "lines":    {"r03": 10220.0, "r09b": 12.59, "r21": 184.77, ...}
    }

## What it is uniquely good for

* **The 1 July 2025 form change.** 32 filings on `DPH2021` and 6 on `DPH2025`,
  switching between 2025-06 and 2025-07 — and the boundary shows on identical
  amounts, which is as clean as evidence gets:

      2025-06  DPH2021  r09  12.59  r10  2.90
      2025-07  DPH2025  r09b 12.59  r10b 2.90

  Nothing about the company changed; the form did.
* **Amendments.** One `dodatočné` return (2023-07, filed 2023-09-24), so the
  amendment path has a real case rather than a synthetic one.
* **The eForm's own line codes** (`r191`, `r211`, `r281`) alongside the ones
  this module emits, which is the translation table a filed-versus-computed
  comparison needs.

## Provenance and scope

Extracted from an MRP-K/S backup by the `legacy_import_mrp` spike, from the
filing register rather than from documents — which is why it reaches back to
2022 while that agenda's documents start in 2023.

It contains period totals only: no counterparty, no document, no name. The
company is Data Dance s.r.o., whose own data this is.
