# currency_rate_update_cz: developer notes

Not user documentation: this file is not rendered into a page.

## Rate parsing

The ČNB publishes one daily exchange-rate fixing (CZK against foreign
currencies). For a CZK-base company the rate stored on `res.currency.rate` is
`Amount / Rate` (foreign units per CZK) — e.g. `EMU|euro|1|EUR|24.170`
becomes `1 / 24.170` and `Japan|yen|100|JPY|13.043` becomes
`100 / 13.043`.
