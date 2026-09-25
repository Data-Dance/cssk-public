# Czech EET 2.0 for Odoo (`l10n_cz_eet2`)

Sends registered-sale data messages to the Czech **EET 2.0** system
(Elektronická evidence tržeb), data-interface **v4.1**, over SOAP + WS-Security.

Target: **Odoo 19.0**. Depends only on `cryptography`, `lxml`, `requests`
(no `zeep`/`signxml` needed — the WS-Security signature is built directly).

## Status
- **`lib/eet2_client.py`** — pure-Python client (build ▸ sign ▸ send ▸ parse).
  **Proven end-to-end against the live government playground**
  (`https://pg.trzbyeet.gov.cz/.../v4`): a production-mode message is accepted and
  returns a POK ending in `-ff` (the playground fictitious marker); a bad
  signature would return error `kod=4`.
- Odoo layer: certificate store, company config, a "message" model with a
  **Send to EET** button, security groups, views, settings.

## Signature profile (spec §5.2, all mandatory)
Sign **only** `<soapenv:Body>` · digest **SHA-256** · signature **RSA-SHA256** ·
canonicalization **Exclusive C14N** · X.509 cert inline in a WS-Security
`BinarySecurityToken` · no Timestamp / WS-Addressing · message ≤ 12 kB.

## Configuration
Settings ▸ Accounting ▸ *Czech EET 2.0*: enable, pick environment
(playground/production), set the taxpayer **EIC** and default **unit id**
(`id_jednotky`), and select an uploaded **certificate**.

Certificates: *EET 2.0 ▸ Configuration ▸ Certificates* — upload the `.p12` and its
password. (Python `cryptography` loads the legacy RC2-40/3DES `.p12` directly; the
system `openssl` CLI would need `-legacy`.)

## Accounting (counter payments)
Contact payments registered outside POS are recorded on **`account.payment`
posting**: flag a journal *EET 2.0 Contact Payments* (Advanced Settings), and any
posted payment in that journal is registered (non-blocking; refunds/outbound sent
as negative `celk_trzba`). The payment form shows the POK/status and a *Send to
EET* button for retries.

## Reliability: scheduled retry (no queue_job needed)
Because EET 2.0 has **no offline PKP/BKP code**, an unsent message is an obligation
to send later. This is handled by a lightweight **`ir.cron`** ("EET 2.0: Send
pending messages", every 2 min) — no extra worker process or OCA `queue_job`
dependency:

- Transactions carry `state` (`to_send` / `retry` → `accepted` / `verified` /
  `rejected` / `error`), `attempt_count`, `next_attempt`.
- The cron sends everything due (`state in (to_send, retry)` and `next_attempt`
  passed), committing per message so one failure never rolls back the batch.
- **Error-aware:** network/transport errors and temporary codes (`kod<0`, `8`)
  are retried with **exponential backoff** (2→4→…→60 min) up to a company-set cap
  (*Max Send Attempts*, default 12); permanent errors (`kod` 3/4/6/7) go straight
  to `rejected`; build/cert errors go to `error`. On a resend `prvni_zaslani` flips
  to `false`.
- **Two-tier by caller:** POS sends synchronously at the till (for the receipt
  POK) and falls back to the cron on failure; `account.payment` enqueues and lets
  the cron send (posting stays fast).

## POS layer
`l10n_cz_eet2_pos` (separate module, depends on this + `point_of_sale`) registers
contact-payment POS orders and prints the POK on the receipt via a **synchronous
send during payment validation**.

## Not yet done (next layers)
- Certificate auto-renewal via the CA EET JWT API (`caeetapi_jwt.yml`).
- Business-rule gate for what is in scope (contact vs. remote, EET OFF opt-out).

See `/home/rex/Odoo/EET2/EET2_CLAUDE.md` for the full verified spec notes.
