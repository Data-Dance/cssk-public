=========
Changelog
=========

All notable changes to **l10n_sk_pos_cash_limit** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-11-10
-------------------------

Added
~~~~~

- Foreign cash at the till is valued at the ECB/NBS rate of the day before
  (§ 6 ods. 1 zákona č. 394/2012 Z. z.); a till whose currency has no known
  rate does not guess one.
- With a customer on the order, the cash that customer already paid that day
  at the company's tills is added (§ 6 ods. 2) and shown in the question; the
  back office adds only the earlier orders.

[19.0.1.0.0] — 2026-11-10
-------------------------

Added
~~~~~

- The Point of Sale asks for confirmation before validating an order that
  takes more than 5 000 € in cash, net of change (§ 4 zákona č. 394/2012 Z. z.),
  and the back-office order form shows the same warning.
