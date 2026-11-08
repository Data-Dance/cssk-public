# l10n_cz_eet2: developer notes

Not user documentation: this file is not rendered into a page.

## Signature profile (spec §5.2, all mandatory)
Sign **only** `<soapenv:Body>` · digest **SHA-256** · signature **RSA-SHA256** ·
canonicalization **Exclusive C14N** · X.509 cert inline in a WS-Security
`BinarySecurityToken` · no Timestamp / WS-Addressing · message ≤ 12 kB.

## Configuration
Settings ▸ Accounting ▸ *Czech EET 2.0*: enable, pick environment
(playground/production), set the taxpayer **EIC** and default **unit id**
(`id_jednotky`), and select an uploaded **certificate**.

Certificates: *EET 2.0 ▸ Configuration ▸ Certificates* — upload the `.p12` and its
password, then **Test certificate**: it sends a verification-mode message
(`overeni=true`) that the gateway validates without recording a sale. A daily
job warns 30/14/7 days before expiry (certificates live 366 days). (Python
`cryptography` loads the legacy RC2-40/3DES `.p12` directly; the system
`openssl` CLI would need `-legacy`.)

### Automatic renewal (CA EET 2.0 API)
An hourly job renews the certificate each company has selected, **N days before
it expires** (*Renew Certificate (days before expiry)* in the settings, default
30, 0 = off), through the CA EET 2.0 API (`caeetapi_jwt.yml`,
`lib/caeet_client.py`). The cycle, visible as the *Renewal* status on the
certificate and pushed along by **Renew with CA EET**:

1. `POST /request/renew`, authorised by a JWT (RS256, `x5t#S256` thumbprint)
   signed with the certificate being renewed, which must still be valid;
2. `GET /request/{reqId}/status` until the CA has issued the follow-up
   (`pollAfterSeconds` / `Retry-After` are honoured; 429 and 5xx defer, they
   never fail the cycle);
3. `claim-download`: the new PKCS#12 and its password are stored as a **new
   certificate record** ("… · renewed <date>", linked both ways);
4. a **verification-mode message** signed with the new certificate goes to the
   gateway; only `kod 0` continues;
5. the company is switched to the new certificate, `ack-download` tells the CA
   to discard its copy, and the old certificate is archived.

If the verification fails, or the CA rejects the request, the old certificate
stays in use, the download stays unacknowledged (the CA keeps it re-claimable
for 30 days) and one activity goes to an EET 2.0 manager; the button retries
the verification with the download already in hand.

Hosts are system parameters: `l10n_cz_eet2.caeet_url_production` (default
`https://ca.caeet.gov.cz/api`) and `l10n_cz_eet2.caeet_url_playground`
(default `https://ca.zkus.caeet.gov.cz/api`). **The playground mapping is our
reading of the spec's "zkušební prostředí"**: the published spec lists three
hosts (testovací, zkušební, produkční) without saying which non-production one
serves playground certificates. Confirm it against the playground kit before
relying on it, and change the parameter if it turns out to be `ca.test`.
Validation happens before the gateway does it: the EIC must be `CZ` + 8–10
digits, every unit id must have the DIS+ shape (2–9 digits ending in 1–4).

## Accounting (counter payments)
Contact payments registered outside POS are recorded on **`account.payment`
posting**: flag a journal *EET 2.0 Contact Payments* (Advanced Settings) to set
the default, and each payment carries its own *EET 2.0 Contact Payment* flag the
cashier can flip — the same bank account receives a QR scanned at the counter
(contact, § 6 ZoET) and the same QR paid from home (not). Flagged payments are
registered on posting (non-blocking; customer refunds paid out are sent as
negative `celk_trzba`; money paid to a supplier is not a sale and is never
registered). The payment form shows the POK/status, a *Send to EET* button for
retries and an *EET 2.0* stat button listing every message the payment produced.

**Storno (§ 8 ZoET).** Resetting a posted payment to draft or cancelling it
reverses a registered sale: a negative message with the same unit, till and
sequence number, dated at the reversal, is queued automatically. Re-posting the
payment registers a new sale. Payments created by closing a POS session are
never registered through the journal flag (the till already did it).

**Staging copies.** `data/neutralize.sql` is picked up by Odoo's database
neutralization (`odoo-bin neutralize`, Odoo.sh staging builds, "duplicate" with
neutralize): it switches EET 2.0 off on every company so a copy of production
never registers sales. Certificates and settings stay, so the copy can be
re-enabled against the playground with a playground certificate.

## Reliability: scheduled retry (no queue_job needed)
Because EET 2.0 has **no offline PKP/BKP code**, an unsent message is an obligation
to send later. This is handled by a lightweight **`ir.cron`** ("EET 2.0: Send
pending messages", every 2 min) — no extra worker process or OCA `queue_job`
dependency:

- Transactions carry `state` (`to_send` / `retry` → `accepted` / `verified` /
  `rejected` / `error`), `attempt_count`, `next_attempt`.
- The cron sends everything due (`state in (to_send, retry)` and `next_attempt`
  passed), committing per message so one failure never rolls back the batch.
- **Error-aware, never gives up (§ 20 ZoET):** network/transport errors and
  temporary codes (`kod<0`, `8`) are retried with **exponential backoff**
  (2→4→…→60 min) until 48 hours after the sale and **hourly after that**; a
  message crossing the 48 h line is flagged *Past 48 h* and raises an activity
  for an EET 2.0 manager. *Warn After Attempts* (default 12) only logs.
  Permanent errors (`kod` 2/3/4/6/7) go to `rejected`; build/cert errors go to
  `error` and are still retried hourly; both are re-queued automatically when a
  certificate is re-uploaded or newly selected, or by hand with *Requeue*. Every
  attempt carries a fresh `uuid_zpravy` and the real `dat_odesl`; on a resend
  `prvni_zaslani` flips to `false` and the Data block never changes (methodology
  ch. 6). Earlier UUIDs are kept on the message.
- **Amounts are CZK** (§ 17 odst. 1 písm. f) ZoET): callers pass their own
  currency, the message converts at the company rate of the sale date and keeps
  the original amount for audit.
- **Two-tier by caller:** POS sends synchronously at the till (for the receipt
  POK), waiting at most the company's *Response Time Limit* (mezní doba odezvy,
  § 19 ZoET, default 5 s, at least 2 s) and falls back to the cron on failure;
  `account.payment` enqueues and lets the cron send (posting stays fast).
