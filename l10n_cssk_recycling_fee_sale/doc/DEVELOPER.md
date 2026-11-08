# l10n_cssk_recycling_fee_sale: developer notes

Not user documentation: this file is not rendered into a page.

## OCA gap

- **Priced at the order date.** Each order line gets the CZ/SK fee of its
  company's market from the rate valid on the order date, per piece in the
  product's unit or per kg. The invoice prices again at the invoice date — the
  invoice is the tax document the law speaks about, and a tariff may have
  changed in between.
* **The product's fixed amount travels to the invoice.** OCA copies only the
  classification and its document-currency override; a distributor's fixed
  amount (what its supplier paid) is carried as well.
* **"On top" presentation.** When the company invoices the fee on top of the
  price (Invoicing settings → *Recycling Fee*), the *Update Recycling Fee* button
  on the order adds one line per classification and VAT treatment with the fee
  product, priced at the summed fee. Pressing it again regenerates the lines;
  once they are invoiced it refuses. Portable-battery fees get no line — CZ § 85
  odst. 3 and SK § 46 ods. 2 forbid stating them separately, so they stay in the
  price. The fee lines take the VAT of the goods they belong to.
