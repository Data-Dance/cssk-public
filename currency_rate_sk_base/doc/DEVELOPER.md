# currency_rate_sk_base: developer notes

Not user documentation: this file is not rendered into a page.

## Fetching

- `fetch_vub_text` / `parse_vub` — VÚB *kurzový lístok* text feed, using the
  **Devíza stred** (middle) rate for accounting valuation.
* `fetch_tb_text` / `parse_tb` — Tatra banka exchange-rate RSS feed, parsed
  over a date range.
* Per-bank supported-currency lists (`VUB_CURRENCIES` / `TB_CURRENCIES`).
* Browser-like User-Agent so the bank endpoints (Tatra banka sits behind
  Cloudflare) do not reject the request.
