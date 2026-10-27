---
title: Intrastat in the Statutory Footprint (CZ/SK)
summary: The statutory footprint of a posted document also names the Intrastat declarations that reported its lines, with their period, flow and state.
verified: 19.0.1.1.0
family: l10n_sk_intrastat#footprint
---

Adds Intrastat to the **Statutory footprint** of posted invoices and journal entries. For every OCA Intrastat declaration that took one of the document's lines, the footprint shows the form *Intrastat*, the period, the flow (arrivals or dispatches) and the declaration's state, with a link to it. It reads the link the declaration stored when its lines were generated, so a month whose declaration has not been generated yet shows nothing.

It installs itself when [module:l10n_cssk_core](module:l10n_cssk_core) and the OCA `intrastat_product` engine are both present — on a database that had both before this module existed, install it once by hand — and has no settings. It does not read Odoo Enterprise's Intrastat report.
