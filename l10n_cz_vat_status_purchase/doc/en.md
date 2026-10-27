---
title: CZ VAT Status — Purchase Orders
summary: Purchase order lines propose the taxes the Czech company's VAT status allows on the order date.
verified: 19.0.1.0.0
family: l10n_cz_vat_status#orders
---

When the company records a VAT status history, a purchase order line — including one created by a reordering rule or make-to-order — proposes the taxes that status allows on the order date, for example the non-deductible variant while the company is a neplátce. It is only a proposal: the vendor bill is decided again by its own DUZP, and cannot be posted with taxes that no longer fit.

It installs itself when both Purchase and the CZ VAT status module are installed, and has no settings.
