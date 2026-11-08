# account_cz_bankfile_base: developer notes

Not user documentation: this file is not rendered into a page.

## Reusing the builders

There are **no Odoo models** here — only pure helpers, imported via
`odoo.addons.account_cz_bankfile_base.utils.*`. The builders take a list of
normalized `BankPaymentItem` records (plain values plus the bank records), so
the edition-specific shims can feed them from either `account.payment.line`
(OCA payment order, CE) or `account.payment` (Enterprise batch payment, EE)
without duplicating any format logic.
