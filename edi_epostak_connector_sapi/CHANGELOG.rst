=========
Changelog
=========

All notable changes to **edi_epostak_connector_sapi** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.1.1] — 2026-10-03
-------------------------

Fixed
~~~~~

- **A 404 from the Peppol directory was treated as a transport failure.**
  *Check Peppol reachability* showed a red failure dialog for the one case it
  exists to report. ePošťák answers an unregistered participant with HTTP
  **404** carrying a complete negative body (``found``/``accepts`` false, a
  ``reason``, and ``capability.routingStatus``); the call passed no
  ``expected``, so it defaulted to ``(200,)`` and raised ``EpostakApiError``
  over a perfectly good answer — while the caller below it was already written
  for exactly that body and never saw one.

  A 404 *without* ``found`` still raises: a changed route is not "participant
  not registered", and reporting it as one would diagnose the wrong thing.

- **``networkReady`` and ``routingStatus`` were never read.** Probing the
  sandbox to confirm the body shape turned this up as a separate defect: both
  the positive and the negative body nest them under ``capability``, never at
  the top level, so ``result.get("networkReady")`` returned ``None`` even on a
  successful lookup and the not-network-ready note could never fire. They are
  lifted in ``_check_capabilities`` now, so its documented return contract
  finally holds.

- The negative outcome is a sticky **warning** quoting the provider's own
  ``reason`` and ``routingStatus`` rather than a red error — the commonest
  cause is a counterparty who has not registered, the second commonest our own
  EAS being wrong, and the message names both. Suppressed on a clean success,
  where ``ready`` only restates the title.

Reported from the field 2026-10-03: the customer's company partner carried
``9950:SK2022913409`` (EAS 9950 is the IČ DPH scheme) while ePošťák knows them
as ``0245:4025578881`` (0245 is the DIČ), so the lookup was correctly negative
— and the dialog hid that behind a traceback.

Verified live against the ePošťák sandbox on both paths. The seven new tests
were negative-controlled against the unfixed source: four fail there,
including the positive-path one, while the three guard tests hold both ways.

Ported to 18.0 on 2026-10-03 as ``0b8eae57`` (``[18.0.1.1.0]``) — **do not
port this again.** The connector change there is byte-identical; that commit
also took down the ``UserError`` wrapper from ``[19.0.1.1.0]``, whose
remaining parts 18.0 still owes and records in its own Carry-over section.


[19.0.1.1.0] — 2026-10-01
-------------------------

Fixed
~~~~~

- **An integrator key with no Firm ID failed as a traceback on every button.**
  A customer on the standalone module configured an ``sk_int_*`` secret, left
  **ePošťák Firm ID** empty, and pressed *Check Peppol reachability*. An
  integrator key speaks for several firms, so the API requires ``X-Firm-Id`` on
  each call and answers ``400 BAD_REQUEST`` without it. The message was a good
  one, but ``EpostakApiError`` is a plain ``Exception``, so it escaped the
  button and reached the user as an RPC traceback instead of a dialog.

  Three changes: ``_assert_firm_scope`` refuses the combination up front — on
  the shared ``_validate_config`` path, so the send/poll/status crons are
  covered too, not only the button — and both interactive buttons now wrap
  ``EpostakApiError`` into ``UserError``. The check is kept as its own method
  rather than inlined so ``_list_firms`` can skip it, and so
  ``edi_epostak_broker_client``'s ``_validate_config`` override keeps its
  signature.

Added
~~~~~

- ``_list_firms()`` — ``GET /firms``, the firms an integrator key may act for.
  It deliberately bypasses ``_validate_config`` and sends no ``X-Firm-Id``:
  this call is how a deployment *finds* the firm id that validation demands, so
  requiring one first would be a closed loop.
- **Test Connection now answers the question it used to only raise.** With an
  integrator key and no Firm ID it lists the firms the key may act for — UUID,
  name and **Peppol id** — so the value can be copied straight into the setting
  instead of looked up in the API docs. The Peppol id is what makes the list
  usable: an integrator acting for several firms picks the right one by matching
  its own Peppol address, where names are easily similar.
- ``/firms`` is minted its **own ``firms:manage`` token**. Our ordinary token is
  ``documents:*`` by design — least privilege for the credential that sends
  invoices all day — and the endpoint answers ``403 INSUFFICIENT_SCOPE``
  without the extra scope, so the firm listing would have failed for exactly
  the customer it was added for. Found by probing the sandbox, not by reading
  the docs. ``_TOKEN_CACHE`` is consequently keyed by scope as well, or a
  documents-only token would be handed to ``/firms`` and vice versa.

- Settings order under *Connection* now follows the setup it describes:
  Configured key → **Test Connection** → Last inbound poll. Offering "Poll
  inbound now" above the button that proves the credentials work put the last
  step first.
- **A repeated inbound failure now raises a to-do for a person.** The Settings
  line only reaches someone who opens Settings and notices the date is old. On
  the third consecutive failed poll (``Warn after N failed polls``, 0 disables)
  a ``mail.activity`` is raised on the company partner — ``res.company`` has no
  activity mixin, and the partner *is* the Peppol participant that is not
  receiving — assigned to an EDI manager, else an EDI user, else the admin, so
  it is never invisible. Not on the first failure, because a blip is normal and
  one activity per poll teaches everyone to ignore them; exactly one, re-used
  and updated with the current count; and **closed automatically** when polling
  succeeds again, because a stale to-do about a fixed problem is how these lose
  their credibility.
- **A key that manages exactly one firm now has its Firm ID filled in.** Test
  Connection used to say "this key speaks for several firms" and ask the user to
  copy a UUID across even when there was only one candidate — untrue, and
  busywork. With one firm it sets the Firm ID and says which firm it chose, in a
  sticky notification, followed by a ``soft_reload`` so the field shows the value
  instead of looking empty and inviting a retype. It must be ``soft_reload`` and
  not ``reload``: the latter "simply reloads the page", which tore the
  notification down before it could be read — reported as "no popup indicating
  success was shown". ``soft_reload`` restores the current controller only, so a
  toast in the root container survives it. With more than one it still asks, and states the real
  count. The refusal message no longer claims plurality either: an integrator
  key "acts on behalf of firms rather than being one".
- **Inbound now reports itself.** Sending has always been visible — a failure
  lands on the invoice's ``edi.message``. Receiving had **no user-facing signal
  at all**: ``edi_base._poll_provider`` swallows any exception from
  ``_poll_inbound`` into the log, and a misconfiguration returned an empty
  result and said nothing. So with the Firm ID blank — the reported ticket —
  sending failed loudly while receiving silently stopped, which is the worse of
  the two. Demonstrated on a queue-less database: two polls, one with no Firm ID
  and one with wrong credentials, both returned normally and created no record
  of any kind.

  Three additions, all in the ePošťák modules:

  * ``_record_poll`` stores the outcome of every poll —
    ``epostak.inbound.last_poll`` / ``last_ok`` / ``last_error`` /
    ``last_count`` — on **both** the success and the failure paths. The last
    success deliberately does not move on a failure: a stale "last OK" beside a
    recent error is the evidence that documents stopped arriving.
  * A **Last inbound poll** line in Settings reads it back: "Never polled",
    "OK at … — N document(s) fetched", or "FAILED at … — <reason> (last
    success: …)".
  * A **Poll inbound now** button, so receiving can be verified during setup
    instead of waiting for a cron and then reading the server log. It reports
    success, "polled but some documents are in error", or the failure.

  A configuration fault during the poll is now logged at ERROR rather than
  warning — it is never transient, and it stops inbound completely.

  The poll button runs with the inbound cron's rights (``sudo``). The settings
  page is gated on ``base.group_system``, but ``edi.message`` is restricted to
  the EDI groups — which an Administrator is not in by default — so the button
  raised an ``AccessError`` for exactly the person who configures the
  connection. It reproduces what the cron does as superuser rather than widening
  anything.
- **Test Connection no longer raises — it reports.** It was raising a
  ``UserError`` to *deliver* the firm list, which renders as a failure ("Test
  Connection stopped working" when the Firm ID was cleared) and, because a raise
  rolls the transaction back, discarded the ``set_values()`` above it — throwing
  away a secret the user had just typed. Every outcome is now a notification:
  success, a ``warning`` carrying the firms to choose from, or a ``danger`` with
  the provider's message. Settings entered in the form always persist.
- **The form now states which kind of key is configured.** The secret renders
  as a password, so a user cannot see its prefix and therefore cannot tell which
  half of the Firm ID help applies to them — which is precisely how the
  2026-10-01 ticket happened: an ``sk_int_*`` key, help saying "only for
  integrator keys", no way to know they had one. A read-only *Configured key*
  line under Connection now says "Integrator key (sk_int_*) — the Firm ID below
  IS required" or "Firm key (sk_live_*) — leave it empty", and names the firm
  once one is set.

Changed
~~~~~~~

- ``_error_detail`` also reads ``request_id`` / ``requestId`` as the support
  handle (the Enterprise errors use it where SAPI uses ``correlation_id``), and
  surfaces ``fix_hint`` when present — on the real 403 it is the most
  actionable sentence in the body.
- Corrected a false claim in ``_list_firms``'s own docstring: it said a firm key
  gets a 403 there and the endpoint is integrator-only. Verified against the
  sandbox on 2026-10-01, a firm key returns its own single firm; the gate is the
  ``firms:manage`` scope, not the shape of the key.

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
