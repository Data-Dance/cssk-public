---
title: CZ Invoice — Payment Method (Forma úhrady)
summary: Prints the invoice's payment mode as "Forma úhrady" next to the payment symbols on the Czech invoice.
verified: 19.0.1.0.0
family: l10n_cz_invoice#payment-mode
---

Prints the invoice's **Payment Mode** under the heading *Forma úhrady* in the row with the invoice dates and payment symbols of the Czech invoice — the place a Czech reader looks for it. Nothing is printed when the invoice has no payment mode or the company is not Czech.

It installs itself when both the Czech invoice layout and OCA's payment modes (`account_payment_mode`) are installed, and has no settings.
