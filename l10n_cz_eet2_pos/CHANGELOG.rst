=========
Changelog
=========

All notable changes to **l10n_cz_eet2_pos** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Fixed
~~~~~

- **One live sale message per POS order**, enforced by the database. The
  message now carries ``pos_order_id`` and a partial unique index mirrors the
  payment one: a sync and a resend racing each other, or two syncs of one
  order from two workers, fail the second insert instead of evidencing the
  sale twice. *Resend to EET* reuses the order's message (requeue + send)
  instead of creating a second one; a storno of a POS message keeps the order
  link. 18.0 owes this fix. DISCHARGED 2026-10-31 by 7f51d0d1 on branch 18.0 (origin/18.0 ea53193a) — do not port this again.
- **Only the contact money is registered.** ``celk_trzba`` is the sum of the
  payment lines made through a method flagged *EET 2.0 Contact Payment*, not
  ``amount_total`` (§ 5–6 ZoET, § 17 odst. 1 písm. f)). An order paid half in
  cash and half through a method flagged remote registers the cash half; an
  order with no contact money, or whose contact lines net to zero, registers
  nothing and says so in its chatter. Change given back is a negative cash
  line and nets out. A refund registers the negative sum of its contact lines.
- **Session-closing payments are never registered.** Closing a POS session
  books the takings as ``account.payment`` records; those sales were already
  registered one by one at the till, so a cash journal flagged *Contact
  Payments* no longer evidences them a second time.

Added
~~~~~

- The receipt prints **"Tržba bude odeslána dodatečně"** when the order is in
  scope (its contact lines do not net to zero, the same test the backend
  applies) but has no POK yet (queued, retrying, or the gateway did not answer
  within the response-time limit); a rejected message prints nothing. The
  contact flag of payment methods is loaded into the point of sale for that.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- **Everything under 19.0.1.1.0 below and the [Unreleased] entries above**, together with ``l10n_cz_eet2``
  19.0.1.1.0 and the new ``l10n_cz_eet2_pos_loyalty``.
  DISCHARGED 2026-10-31 by 7f51d0d1 on branch 18.0 (origin/18.0 ea53193a) — do not port this again.

[19.0.1.1.0] — 2026-10-29
-------------------------

Fixed
~~~~~

- ``dat_trzby`` is the time of the payment (latest ``payment_date`` on the
  order), not the time the order was opened: § 16 odst. 2 ZoET places the sale
  at the moment the payment is received or ordered, and a restaurant table can
  sit open for hours.
- The synchronous send at the till now waits at most the company's *Response
  Time Limit* (mezní doba odezvy, § 19 ZoET) instead of a hard-coded 10 s; on a
  timeout the sale goes through and the scheduled job resends.
- A point of sale in another currency sent its totals unconverted; the base
  module now converts to CZK.
- README no longer claims the receipt fields are exposed through
  ``_load_pos_data_fields`` two paragraphs above the note that forbids overriding
  it.

Added
~~~~~

- ``_l10n_cz_eet2_amounts()`` hook so bridges can fill ``urceno_cerp_zuct`` /
  ``cerp_zuct`` (used by ``l10n_cz_eet2_pos_loyalty`` for gift cards and
  eWallets).
- The point-of-sale unit id is validated against the DIS+ shape.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Registers Point-of-Sale payments with the Czech EET 2.0 system, extending
  ``l10n_cz_eet2`` into POS.
- Per-payment-method EET flag on ``pos.payment.method`` and EET settings on
  ``pos.config``; ``pos.order`` carries the registration and its returned codes.
- Prints the POK (potvrzení o evidenci — proof of registration) on the receipt via
  a POS receipt template override.
