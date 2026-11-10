=========
Changelog
=========

All notable changes to **l10n_sk_pos_cash_limit** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.1.0] — 2026-11-10
-------------------------

Added
~~~~~

- Ported from 19.0.1.1.0: foreign cash at the till valued at the ECB/NBS
  rate of the day before (§ 6 ods. 1 zákona č. 394/2012 Z. z.), and the
  cash the customer already paid that day added up (§ 6 ods. 2). On 18.0 the
  till asks the server once per validation for the rate, the limit and the
  customer's earlier cash; offline a euro till checks the order alone.

[18.0.1.0.0] — 2026-11-10
-------------------------

Added
~~~~~

- Ported from 19.0.1.0.0. The Point of Sale asks for confirmation before
  validating an order that takes more than 5 000 € in cash, net of change
  (§ 4 zákona č. 394/2012 Z. z.), and the back-office order form shows the
  same warning.
