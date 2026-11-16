---
title: SK DPPO itemised Table A
summary: Evidenced expense items feed the native versioned Table A return rows, without replacing tax depreciation or filing history.
verified: 19.0.1.0.1
---

## Purpose {#purpose}

This workpaper groups non-deductible expense items into the selected DPPO version's Table A input rows. It requires l10n_sk_dppo 19.0.1.5.0 and l10n_cssk_income_tax_base 19.0.1.6.0 or newer. Native return lines remain the only tax calculation: a17 (a15 on 2013/2014) feeds r130; Table B and r150/r250 remain owned by the native depreciation register and manual return inputs.

## Workflow {#workflow}

Enable the workpaper, choose each expense row, enter the amount and evidence, review the complete workpaper and compute the return. Multiple items on the same row are added. Native captions identify the applicable row. Each form is validated against its own input definitions, so an older form's aggregate cannot be used as an expense row.

Only rows with workpaper items are managed. Other manually entered Table A rows and all Table B rows remain available. While enabled, item sums replace the corresponding manual overrides. Removing an item or disabling the workpaper releases its previous generated overrides on recompute; a manual amount changed independently is retained. Recompute before export if item sums changed.

The same current-workpaper check applies to XML, the native official paper
PDF when available, and posting the tax provision. A changed workpaper must
be recomputed before those outputs can use its amounts. Historical downloaded
attachments remain available. Adding items for several returns validates the
whole batch before changing any of them.

## Amendments and filing {#amendments}

The native amendment action copies the items and the ordinary overridden return rows. Review status and review evidence are cleared, so review the changed workpaper independently and recompute. The native submission framework retains filed XML. This module does not override attachments, download streams, Table B XML templates or the tax spine. Changes to the company or posting the tax provision do not prevent downloading previously exported bytes.

## Scope {#scope}

Evidence and legal deductibility are accounting decisions; entering an item does not certify them. No second ledger, full-ledger signature or separate filing archive is created.
