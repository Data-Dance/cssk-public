# Czech EET 2.0 — Point of Sale (`l10n_cz_eet2_pos`)

Registers Point-of-Sale **contact payments** with the Czech EET 2.0 system and
prints the returned **POK** on the receipt. Odoo 19.0. Depends on `l10n_cz_eet2`
and `point_of_sale`.

## How it works
- **Registration.** When the frontend syncs an order
  (`pos.order.sync_from_ui` → `_process_order`), a paid, in-scope order is sent to
  EET 2.0 via the base `l10n.cz.eet2.transaction` model. Registration **never
  blocks the sale** — failures are logged and can be resent.
- **Synchronous send for the receipt.** The payment-validation flow is patched
  (`beforePostPushOrderResolve`): after the order is pushed, the frontend blocks
  the UI and calls `get_l10n_cz_eet2_pos_data` (idempotent register + return POK),
  attaching the POK to the order **before** the receipt renders. So the printed
  receipt reliably carries the POK, not just orders reloaded later.
- **Scope.** An order is in scope when the company has EET 2.0 enabled and its
  payment lines made through a method flagged *EET 2.0 Contact Payment* (cash,
  card, QR — on by default; turn off for remote/out-of-scope methods) add up to
  something other than zero. **Only that contact sum is registered**, not
  `amount_total` (§ 5–6 ZoET): an order paid half in cash and half through a
  method flagged remote registers the cash half; one with no contact money
  registers nothing and says so in its chatter. Change given back is a negative
  cash line and nets out; a refund registers the negative sum of its contact lines.
- **Session closing.** The payments Odoo books when a POS session closes carry
  `pos_session_id` and are never registered through a journal's *Contact
  Payments* flag: the till already registered every order.
- **Offline notice.** When the order is in scope but has no POK yet (queued,
  retrying, or the gateway did not answer within the response-time limit) the
  receipt prints *"Tržba bude odeslána dodatečně"*; a rejected message prints
  nothing. The payment methods' contact flag is loaded into the frontend for this.
- **Receipt.** `l10n_cz_eet2_pok`, `l10n_cz_eet2_state`, `l10n_cz_eet2_is_test` are
  stored related fields on `pos.order`, so the frontend receives them with the
  default (unrestricted) `pos.order` read; the receipt shows the POK (and a TEST
  marker in the playground) once the order sync returns it. Nothing overrides
  `_load_pos_data_fields` — see the maintainer note below.
- **One live sale per order.** The message carries `pos_order_id`, and a
  partial unique index refuses a second live sale message for the same order;
  resend reuses the existing message.
- **Resend.** The backend POS order form has a *Resend to EET* button for orders
  not yet accepted (e.g. after a temporary error `kod<0`). EET 2.0 has **no offline
  PKP/BKP code** — offline handling is resend-based.

## Configuration
- **POS ▸ Configuration ▸ Point of Sale**: set *EET 2.0 PoS ID* (`id_pokl`, ≤20
  chars; falls back to the POS name) and optionally the unit id (`id_jednotky`).
- **POS ▸ Configuration ▸ Payment Methods**: toggle *EET 2.0 Contact Payment*.
- Company-level EIC, environment and certificate come from the base module.

## Field mapping (order → Trzba)
`eic_popl`←company · `id_jednotky`←config/company · `id_pokl`←config/name ·
`porad_cis`←`pos_reference` (sanitized ≤25) · `dat_trzby`←latest
`payment_ids.payment_date` (falls back to `date_order`) · `celk_trzba`←
the sum of the contact payment lines, converted to CZK by the base module when the POS runs in another
currency. Gift-card / eWallet top-ups and redemptions are mapped to
`urceno_cerp_zuct` / `cerp_zuct` by `l10n_cz_eet2_pos_loyalty`.

## Notes
The synchronous send blocks the UI during payment validation for at most the
company's *EET 2.0 Response Time Limit* (mezní doba odezvy, § 19 ZoET, default
5 s). If the POK does not arrive in time the sale still completes and the
scheduled job keeps resending until the gateway accepts it (§ 20 ZoET: at the
latest within 48 hours, and the duty does not lapse after that), so there is
nothing to do at the till; the order can also be resent manually from the backend.

**Maintainer note — do NOT override `pos.order._load_pos_data_fields`.** Its base
returns `[]`, which `read()` treats as "all fields", so our stored related fields
(`l10n_cz_eet2_pok/state/is_test`) already reach the frontend. Returning a
non-empty list from an override restricts the read and drops `lines`/`payment_ids`,
crashing POS price computation (`this.lines` undefined → `_computeAllPrices`).
Verified end-to-end: a cash sale prints the POK on the receipt.
