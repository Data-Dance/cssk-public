==============================
Currency Rate Update CZ (ČNB)
==============================

Adds the **Česká národní banka** (Czech National Bank) daily fixing as a
``res.currency.rate.provider`` to the OCA ``currency_rate_update`` framework.
CE-compatible — it does **not** depend on the Odoo Enterprise
``currency_rate_live`` feature.

The ČNB publishes one daily exchange-rate fixing (CZK against foreign
currencies). For a CZK-base company the rate stored on ``res.currency.rate`` is
``Amount / Rate`` (foreign units per CZK) — e.g. ``EMU|euro|1|EUR|24.170``
becomes ``1 / 24.170`` and ``Japan|yen|100|JPY|13.043`` becomes
``100 / 13.043``.

This module derives from the AGPL ``currency_rate_update`` framework and is
therefore licensed AGPL-3.

Features
========

* **ČNB** daily-fixing provider for ``currency_rate_update``.
* Correct CZK-base conversion that honours the per-currency unit (``Amount``
  column, e.g. 100 JPY).
* Works on Odoo Community — no Enterprise live-rate dependency.

Usage
=====

In *Settings ▸ Technical ▸ Currency Rate Providers* (or
*Invoicing/Accounting ▸ Configuration ▸ Currency Rate Providers*) create a
provider, choose **Česká národní banka (ČNB)** as the service, select the
currencies to track, and run the sync (manually or via the scheduled action).
The pulled rates are written to ``res.currency.rate``.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3 (see the LICENSE file).
