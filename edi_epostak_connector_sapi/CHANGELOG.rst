=========
Changelog
=========

All notable changes to **edi_epostak_connector_sapi** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.1] — 2026-08-22
-------------------------

- ``_stamp_failure`` now delegates to ``edi.message._write_outside_job``, so
  the durable-write logic has one implementation shared with the Editel
  connector rather than two.
- **Fix: error bodies rendered as a raw Python dict.** ePošťák nests its error
  one level down (``{"error": {"category", "code", "message", "retryable",
  "correlation_id"}}``); reading the top level only stringified that whole dict
  into the message shown on the record. The nested object is now unwrapped, and
  the ``correlation_id`` — the first thing ePošťák support asks for — is
  included in the message.
- The API states ``retryable`` itself; that is now trusted over our status-code
  heuristic when present, so a non-retryable 409 no longer burns five attempts.

[19.0.1.0.0] — 2026-08-22
-------------------------

- Initial release. Full SAPI-SK 1.0 transport: OAuth 2.0 client-credentials
  auth with a per-process token cache, ``POST /document/send``,
  cursor-paginated ``GET /document/receive`` + per-document payload fetch,
  ``POST /document/receive/{id}/acknowledge``, and delivery-status polling on
  the Enterprise ``GET /documents/{id}/status`` (30-minute cron), since a 202
  from send is intake and not proof of delivery.
- Content-addressed ``Idempotency-Key`` (``uuid5`` over the payload digest,
  not scoped by record id) so a retry — or a second record carrying the same
  invoice — collapses server-side, while a corrected re-send onto the same
  ``edi.message`` is not refused as an idempotency-key mismatch.
- Send failures are persisted on a separate cursor. queue_job rolls the job
  cursor back before recording a failure and forbids committing it, so the
  obvious inline ``write(state='error')`` is discarded — the message would sit
  in ``queued`` with no error text beside a failed job.
- Untrusted remote text (error bodies, status reasons) is stripped of control
  characters and collapsed before it reaches the log or ``error_message``, and
  provider-supplied ids are URL-quoted into request paths.
- Centralised error classification: retryable (409/423/429/5xx) vs permanent,
  with ``Retry-After`` honoured and 429 not spending a retry attempt.
- Partner-form **Check Peppol reachability** button against
  ``POST /peppol/capabilities``, and a **Test Connection** button in settings.

- *Live-validated* 2026-08-22 against the ePošťák sandbox
  (``dev.epostak.sk``) from a throwaway Odoo 19 database: token mint, send,
  delivery-status promotion ``sent`` → ``done``, inbound poll, vendor-bill and
  credit-note import, acknowledge, and duplicate suppression on re-poll. 27
  unit tests green.
