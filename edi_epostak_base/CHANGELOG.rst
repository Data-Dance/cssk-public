=========
Changelog
=========

All notable changes to **edi_epostak_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-08-22
-------------------------

- Initial release. Registers the ``epostak`` provider on ``edi.message``
  (connector + poll cron in ``PROVIDER_CONNECTOR_MAP`` / ``PROVIDER_CRON_MAP``),
  stamps ``provider_mode`` at create time so a document prepared in the sandbox
  is never later transmitted or chased for status against production, and
  extends ``_compute_is_test_mode`` so sandbox traffic is badged as test.
- ``epostak.connector``: environment configuration and Peppol addressing —
  participant identifiers (``scheme:value``, with the
  ``iso6523-actorid-upis::`` prefix normalised away) and UBL introspection
  yielding the document type id, process id and both participants straight out
  of the payload, which is what the API's ``SAPI-DOC-025`` rule requires.
- Inbound poll cron scoped to ``_get_messages("epostak")`` so it does not also
  drain other providers' mailboxes.

- *Live-validated* 2026-08-22 against the ePošťák sandbox
  (``dev.epostak.sk``) from a throwaway Odoo 19 database: token mint, send,
  delivery-status promotion ``sent`` → ``done``, inbound poll, vendor-bill and
  credit-note import, acknowledge, and duplicate suppression on re-poll. 27
  unit tests green.
