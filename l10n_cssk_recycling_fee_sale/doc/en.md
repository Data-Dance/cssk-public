---
title: CZ/SK Recycling Fee on Sales Orders
summary: Prices the CZ/SK recycling fee on sales order lines, carries it to the invoice, and in on-top mode invoices it as its own line.
verified: 19.0.1.0.0
family: l10n_cssk_recycling_fee#sales-orders
---

Prices the statutory recycling fee on each sales order line from the rate valid on the order date, with the same market filter and unit conversion as on invoices, and carries a distributor's fixed amount from the product to the invoice, which prices the fee again at its own date. When the company invoices the fee on top of the price, the **Update Recycling Fee** button on the order adds one fee line per classification and VAT treatment with the configured **Recycling Fee Product**; portable-battery fees never get a line.

It installs itself when [module:l10n_cssk_recycling_fee](module:l10n_cssk_recycling_fee) and OCA `account_ecotax_sale` are both installed. Its only setting, the fee product, appears in the *Recycling Fee* block of the accounting settings when the on-top presentation is chosen.
