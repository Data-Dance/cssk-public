=========
Changelog
=========

All notable changes to **edi_epostak_connector_sapi** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[18.0.1.1.0] — 2026-10-03
-------------------------

Fixed
~~~~~

- **A 404 from the Peppol directory was treated as a transport failure.**
  *Check Peppol reachability* showed a failure for the one case it exists to
  report. ePošťák answers an unregistered participant with HTTP **404**
  carrying a complete negative body (``found``/``accepts`` false, a ``reason``,
  and ``capability.routingStatus``); the call passed no ``expected``, so it
  defaulted to ``(200,)`` and raised over a perfectly good answer — while the
  caller below it was already written for exactly that body and never saw one.

  A 404 *without* ``found`` still raises: a changed route is not "participant
  not registered", and reporting it as one would diagnose the wrong thing.

- **``networkReady`` and ``routingStatus`` were never read.** Both the positive
  and the negative body nest them under ``capability``, never at the top level,
  so ``result.get("networkReady")`` returned ``None`` even on a successful
  lookup and the not-network-ready note could not fire. They are lifted in
  ``_check_capabilities`` now, so its documented return contract holds.

- The negative outcome is a sticky **warning** quoting the provider's own
  ``reason`` and ``routingStatus`` rather than a red error — the commonest
  cause is a counterparty who has not registered, the second commonest our own
  EAS being wrong, and the message names both. Suppressed on success, where
  ``ready`` only restates the title.

- ``action_epostak_check_peppol`` now wraps ``EpostakApiError`` into
  ``UserError``. This came down from 19.0's ``[19.0.1.1.0]`` ahead of the rest
  of that release, because without it the raise paths above reach the user as
  an RPC traceback rather than a dialog.

Ported from 19.0 ``cdae05de``; the connector change is identical, and the only
18.0-side addition is the ``UserError`` wrapper noted above. Verified live
against the ePošťák sandbox on both the negative and the positive path, and the
seven new tests were negative-controlled against the unported source (four
fail, including the positive-path one). Suite: 24 tests, 0 failed.

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

The **rest** of 19.0's ``[19.0.1.1.0]`` is still owed here and was deliberately
not brought down in this commit:

- ``_assert_firm_scope`` — an ``sk_int_*`` integrator key with an empty
  **ePošťák Firm ID** is refused up front, on the shared ``_validate_config``
  path so the crons are covered too. Without it, 18.0 still fails every call
  with a raw ``400 BAD_REQUEST`` naming ``X-Firm-Id``.
- ``_list_firms()`` (``GET /firms``, scope ``firms:manage``) and the Test
  Connection behaviour built on it, which lists the firms a key may act for so
  the Firm ID can be copied into the setting.
- ``_record_poll`` / inbound-health reporting and the poll-failure activity.
- ``epostak_key_kind``, the settings-form wording, and ``soft_reload``.

Only the 404 fix was in scope on 2026-10-03.


[18.0.1.0.1] — 2026-08-23
-------------------------

Added
~~~~~

- Back-ported from the 19.0 branch unchanged; no API deltas. OCA ``queue_job``
  18.0 has the same ``_prevent_commit`` + ``env.cr.rollback()`` semantics as
  19.0, so the ``_write_outside_job`` rationale holds verbatim.


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
