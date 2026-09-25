========================
Currency Rate Update SK
========================

Slovak exchange-rate **providers** for the OCA ``currency_rate_update``
framework. CE-compatible — does **not** depend on Odoo Enterprise
``currency_rate_live``.

Providers
=========

==============  =========================================================  =================
Service         Source                                                     Use
==============  =========================================================  =================
ECB *(base)*    ECB reference rate (NBS republishes it for SK)             **Statutory** FX valuation
VÚB banka       ``https://www.vub.sk/Downloads/VUBteclist.txt`` (stred)    Commercial / bank reconciliation
Tatra banka     RSS at ``tatrabanka.sk/.../exchange-rates/``               Commercial / bank reconciliation
==============  =========================================================  =================

The **ECB** provider ships in the OCA base module; this add-on contributes the
two Slovak commercial banks plus the previous-day fill below.

Previous-day fill
=================

Banks and the ECB do not publish on weekends and holidays. With **Fill
non-publishing days** enabled (default, per-provider toggle), after each sync
the last published rate is carried forward to every calendar day in the synced
window, so every day has an explicit ``res.currency.rate`` and no posting lands
on a day without a rate. The fill is idempotent and never overwrites a published
rate.

Notes & limitations
====================

* **VÚB** uses the *Devíza stred* (middle) column — the rate appropriate for
  accounting valuation (the legacy 18.0 module read the *predaj*/sell column).
* **Tatra banka** is, as of 2026-06, behind a Cloudflare bot challenge that
  returns HTTP 403 to non-browser clients. A server-side scheduled fetch will
  fail until the host can pass the challenge (e.g. an IP allow-list with TB, or
  a headless-browser/proxy fetch). The provider code is correct and will work
  against the documented feed once it is reachable.
* **Statutory caveat (needs accountant sign-off):** SK law values a
  foreign-currency transaction at the ECB reference rate of the *preceding*
  business day. Odoo's rate lookup returns the latest rate dated on-or-before
  the transaction date, so when a same-day ECB rate exists it is used rather
  than the prior day's. Aligning strictly with the "preceding day" rule would
  require posting each ECB rate under the following day's date — not done here;
  raise with the customer's accountant before enabling.

License
=======

AGPL-3 (derives from the AGPL ``currency_rate_update`` framework).
