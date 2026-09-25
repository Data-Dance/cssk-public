=============================
ePošťák Connector: SAPI-SK 1.0
=============================

Concrete transport for the ePošťák access point, speaking **SAPI-SK 1.0**
(REST/JSON over HTTPS). Docs: https://epostak.sk/api/docs.

Why SAPI and not the Enterprise API
===================================

ePošťák exposes two surfaces. The **Enterprise API** (``/api/v1``) models an
invoice as JSON and builds the UBL for you; **SAPI** (``/sapi/v1``) takes the
Peppol XML as an opaque payload. This stack already holds a valid, validated
BIS3 document produced by ``account.edi.xml.ubl_bis3`` (or a national subclass
such as ``account.edi.xml.ubl_sk``), so SAPI is a direct fit — the Enterprise
JSON model would mean re-deriving an invoice we already have, and losing
whatever the national builder added on the way.

Two lifecycle endpoints have no SAPI equivalent and are called on the
Enterprise base URL with the *same* token, best-effort:

* ``GET /documents/{id}/status`` — delivery outcome (cron, every 30 min);
* ``POST /peppol/capabilities`` — participant reachability preflight.

A key scoped to ``documents:send`` alone is refused there; that disables
tracking for the run and never breaks sending.

What it implements
==================

============================  ==================================================
``_authenticate``             ``POST /auth/token`` (OAuth 2.0 client credentials)
``_send_message``             ``POST /document/send``
``_poll_inbound``             ``GET /document/receive`` + ``GET …/{id}``
``_acknowledge_inbound``      ``POST /document/receive/{id}/acknowledge``
``_query_status``             ``GET /documents/{id}/status`` (Enterprise)
``_check_capabilities``       ``POST /peppol/capabilities`` (Enterprise)
============================  ==================================================

Behaviours worth knowing
========================

* **202 is intake, not delivery.** A successful send leaves the message in
  ``sent``; only the status cron promotes it to ``done`` (delivered) or
  ``error`` (rejected / send_failed / delivery_failed / validation_failed).
* **The Idempotency-Key is content-addressed** — ``uuid5`` over the payload
  digest, not a random UUID stored once, and deliberately not scoped by the
  record id. A retry of the same bytes presents the same key, so a send that
  succeeded before timing out is collapsed rather than delivered twice; two
  records carrying the same invoice collapse too. A document regenerated after
  a correction — which ``_peppol_emit`` writes onto the *same* ``edi.message``
  — hashes differently and gets a new key, instead of being refused for ever
  as an ``IDEMPOTENCY_KEY_MISMATCH``.
* **A failure is written on its own cursor.** queue_job rolls the job cursor
  back before recording the failure, and forbids committing it, so stamping
  ``state='error'`` inline would be discarded and leave the message in
  ``queued`` with no error text next to a failed job. ``_stamp_failure`` rolls
  back first — releasing the row locks a second cursor would deadlock on —
  then writes and commits separately.
* **Tokens are re-minted, never rotated.** Refresh-token rotation is one-shot,
  and the token cache is per worker process; two Odoo workers sharing
  credentials would invalidate each other's tokens and flap. A
  client_credentials mint has no shared state.
* **Retry policy is decided once**, in ``_request``: 409/423/429/5xx are
  retryable unless the body names a permanent code; a 401 is retried exactly
  once against a freshly minted token. Permanent failures raise
  ``FailedJobError`` rather than burning five retries.
* **Nothing is acknowledged before it is stored.** A document whose payload
  cannot be fetched is left ``RECEIVED`` on the server and reappears next poll.
* **Sender comes from the document.** The ``X-Peppol-Participant-Id`` header is
  the UBL's own EndpointID, since the API rejects a mismatch
  (``SAPI-DOC-025``); a disagreement with the company's configured address is
  logged.

Configuration
=============

#. *Settings ▸ EDI ▸ ePošťák*: pick the environment, paste the client ID and
   client secret for it, then press **Test Connection**.
#. Set the company partner's Peppol EAS + endpoint (see ``edi_epostak_base``).
#. Install ``edi_epostak_peppol`` to route Peppol documents over this
   transport.
#. On a counterparty, **Check Peppol reachability** on the partner form
   verifies the EAS/endpoint against the Peppol directory before you post an
   invoice to it.

Sandbox
=======

``https://dev.epostak.sk/sapi/v1`` is free and unmetered. Sandbox credentials
are rejected by the production host by design, so both credential sets are
stored separately and the environment switch is all that changes.
