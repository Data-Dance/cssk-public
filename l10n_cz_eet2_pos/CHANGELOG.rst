=========
Changelog
=========

All notable changes to **l10n_cz_eet2_pos** are documented here.
Versioning follows the Odoo manifest (``17.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Port from 18.0 (17.0 adaptations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Carried over from ``l10n_cz_eet2_pos`` 18.0.1.3.0 on 2026-11-13; the
  functional scope is the same. 17.0 differences:

  - The frontend patches the 17.0 ``Order`` model
    (``@point_of_sale/app/store/models``): ``export_for_printing`` hands the
    receipt the EET values, ``wait_for_push_order`` answers yes on an
    EET-enabled till (17.0 runs ``PaymentScreen._postPushOrderResolve``, where
    the POK is fetched, only for orders that ask for it) and
    ``init_from_JSON`` takes the POK of an order reloaded from the server, so
    a receipt reprinted from the ticket screen shows it as well
    (``pos.order._export_for_ui``).
  - The payment methods' contact flag reaches the till through
    ``pos.session._loader_params_pos_payment_method`` (18.0:
    ``_load_pos_data_fields``).
  - ``_process_order`` has the 17.0 signature ``(order, draft,
    existing_order)``; an order synced as a draft is not registered.
  - ``pos.order`` has no chatter on 17.0, so the note for an order whose
    contact payments add up to zero goes to the server log.

Fixed
~~~~~

- **One live sale message per POS order**, enforced by the database. The
  message now carries ``pos_order_id`` and a partial unique index mirrors the
  payment one: a sync and a resend racing each other, or two syncs of one
  order from two workers, fail the second insert instead of evidencing the
  sale twice. *Resend to EET* reuses the order's message (requeue + send)
  instead of creating a second one; a storno of a POS message keeps the order
  link. Port of 19.0.1.3.0; on 18.0 the partial unique index is created in
  ``init()`` since ``models.UniqueIndex`` does not exist.
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

Port from 19.0 (18.0 adaptations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Carried over from ``l10n_cz_eet2_pos`` 19.0.1.1.0 and 19.0.1.2.0 on
  2026-10-31. On 18.0 the receipt component receives only the printing data
  (``props.data``), not the order, so the POK, state, test flag and the
  in-scope test are added to that data by an ``export_for_printing`` override
  (``static/src/overrides/models/pos_order.js``) and the receipt template reads
  them from there; the payment-validation hook stays
  ``PaymentScreen._postPushOrderResolve``.

[18.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Registers Point-of-Sale payments with the Czech EET 2.0 system, extending
  ``l10n_cz_eet2`` into POS.
- Per-payment-method EET flag on ``pos.payment.method`` and EET settings on
  ``pos.config``; ``pos.order`` carries the registration and its returned codes.
- Prints the POK (potvrzení o evidenci — proof of registration) on the receipt via
  a POS receipt template override.
