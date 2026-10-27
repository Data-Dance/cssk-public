---
title: CZ/SK Intrastat — File Renderer (Base)
summary: The shared code that renders the Slovak INSTAT XML and the Czech InstatOnline CSV for the Intrastat modules of both editions.
verified: 19.0.1.1.0
family: l10n_sk_intrastat#engine
---

Renders the files the Intrastat modules hand to the authorities: the Slovak **INSTAT XML** message, validated against the bundled official schema `instat62.xsd` (one declaration per file, or an envelope with several), and the Czech **InstatOnline CSV**. It splits the two-digit nature of transaction into the A and B codes INSTAT expects and rounds mass, quantity and value to whole numbers as the schema requires.

It has no screens or settings and depends only on `base`. It installs automatically with [module:l10n_sk_intrastat](module:l10n_sk_intrastat), [module:l10n_sk_intrastat_ee](module:l10n_sk_intrastat_ee) or [module:l10n_cz_intrastat_oca](module:l10n_cz_intrastat_oca).
