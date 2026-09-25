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
- **Scope.** An order is in scope when the company has EET 2.0 enabled and at least
  one payment uses a payment method flagged *EET 2.0 Contact Payment* (cash, card,
  QR — on by default; turn off for remote/out-of-scope methods).
- **Receipt.** `l10n_cz_eet2_pok`, `l10n_cz_eet2_state`, `l10n_cz_eet2_is_test` are
  exposed via `_load_pos_data_fields`; the receipt shows the POK (and a TEST marker
  in the playground) once the order sync returns it.
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
`porad_cis`←`pos_reference` (sanitized ≤25) · `dat_trzby`←`date_order` ·
`celk_trzba`←`amount_total`.

## Notes
The synchronous send blocks the UI briefly during payment validation while the POK
is fetched. If EET is unreachable, the sale still completes and the order can be
resent from the backend (there is no offline PKP/BKP code in EET 2.0).

**Maintainer note — do NOT override `pos.order._load_pos_data_fields`.** Its base
returns `[]`, which `read()` treats as "all fields", so our stored related fields
(`l10n_cz_eet2_pok/state/is_test`) already reach the frontend. Returning a
non-empty list from an override restricts the read and drops `lines`/`payment_ids`,
crashing POS price computation (`this.lines` undefined → `_computeAllPrices`).
Verified end-to-end: a cash sale prints the POK on the receipt.
