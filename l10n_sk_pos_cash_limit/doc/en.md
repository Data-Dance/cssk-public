---
title: Slovakia — Cash Payment Limit at the Point of Sale
summary: Asks the cashier for confirmation before a Point of Sale order takes more than 5 000 € in cash, and flags such orders in the back office.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Slovak law forbids a cash payment above 5 000 €, and a sale at the till is no
exception: the 15 000 € limit applies only between individuals who are not in
business. When the cash on an order, net of the change given back, exceeds
5 000 €, the payment screen stops before validating and asks the cashier to
confirm. "Back" returns to the payment screen to take the rest by card or
transfer; "Continue" validates the order. The back-office order form then
shows the same warning, so such orders can be found and checked.

It installs itself when both
[module:l10n_sk_invoice](module:l10n_sk_invoice) and Point of Sale are present,
and it warns rather than blocks, as the payment warning of that module does.

## Legal background {#legal}

- [Zákon č. 394/2012 Z. z.](law:sk/2012/394), § 4 ods. 1: a cash payment above
  5 000 € is forbidden; ods. 2 raises the limit to 15 000 € only between
  individuals not in business.
- § 8 lists exemptions, such as payments in tax administration or enforcement
  proceedings, which a till cannot recognise; hence a confirmation, not a block.

## Limits {#limits}

The till asks only when the point of sale works in euro; in another currency
the back office still converts and flags the order. One order is one payment:
several receipts of one deal (§ 6 ods. 2) are not added up at the till.
