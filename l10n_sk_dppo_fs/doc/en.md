---
title: SK DPPO — Comparison with the Financial Statements
summary: Compares row r100 of the Slovak income tax return with the profit before tax in the financial statements of the same period.
verified: 19.0.1.1.3
family: l10n_sk_dppo#zavierka
---

Adds the button **Porovnať s účtovnou závierkou** to a computed Slovak income tax return. It finds the company's financial statements (*Účtovná závierka UZPODv14 (SK)*) covering the period and compares r100 of the return with row 56 of the *výkaz ziskov a strát*, the profit before tax. The two must agree to within 0.50 €; the result is kept on the return as a comparison.

It installs itself when the Slovak income tax return, the Slovak financial statements and the Slovak localization bundle (`l10n_sk_datadance`) are all installed, and has no settings.
