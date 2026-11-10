---
title: Slovakia — Cash Payment Limit at the Point of Sale
summary: Asks the cashier for confirmation before a Point of Sale order takes more than 5 000 € in cash, and flags such orders in the back office.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Slovak law forbids a cash payment above 5 000 €, and a sale at the till is no
exception: the 15 000 € limit applies only between individuals who are not in
business. When the cash on an order, net of the change given back, exceeds
5 000 €, the payment screen stops before validating and asks the cashier to
confirm. "Back" returns to the payment screen to take the rest by card or
transfer; "Continue" validates the order. The back-office order form then
shows the same warning, so such orders can be found and checked.

**Foreign cash** is valued in euro at the ECB or NBS rate valid on the day
before the payment (§ 6 ods. 1), which the till receives when it opens. A till
in a currency with no known rate does not guess one and does not ask.

**The same customer paying cash again that day.** The tax authority's guidance
treats one purchase paid in parts as one payment, but separately concluded
purchases as separate ones (pokyn k zákonu 394/2012, čl. 2.3, príklady 15 and
17). A till cannot tell the two apart, so when an order has a customer, the
cash that customer already paid at any of the company's tills that day is
added and shown in the question; the cashier decides. The back office adds
only the earlier orders, so the first order of a series stays unflagged.

It installs itself when both
[module:l10n_sk_invoice](module:l10n_sk_invoice) and Point of Sale are present,
and it warns rather than blocks, as the payment warning of that module does.

## Legal background {#legal}

- [Zákon č. 394/2012 Z. z.](law:sk/2012/394), § 4 ods. 1: a cash payment above
  5 000 € is forbidden; ods. 2 raises the limit to 15 000 € only between
  individuals not in business.
- § 6 ods. 1: foreign cash at the reference rate of the preceding day;
  ods. 2: parts of one payment arising from one legal relationship add up.
- § 8 lists exemptions, such as payments in tax administration or enforcement
  proceedings, which a till cannot recognise; hence a confirmation, not a block.

## Limits {#limits}

Orders without a customer are checked one by one, and parts of one purchase paid on different days are not added up. A cash refund above 5 000 € is asked about too: paying it out is a cash payment as well, but it is never added to the customer's payments. Offline, the till checks the
order alone and the back office adds up later. The rate is the one of the day
before the till was opened; a session left open past midnight keeps it.
