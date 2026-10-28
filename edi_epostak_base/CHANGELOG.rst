=========
Changelog
=========

All notable changes to **edi_epostak_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.1.0] — 2026-10-27
-------------------------

Changed
~~~~~~~

- **The ePošťák Firm ID belongs to the company.** It was one global setting, so
  a second company's documents went out under the first company's firm. It is
  now set per company in *Settings → EDI* (the company you are working in); the
  upgrade gives the old value to the company the inbound scheduled action ran
  as. The environment (sandbox / production) stays database-wide.
- **Every company's inbox is collected.** The inbound scheduled action used to
  ask for the documents of one company only — that of its user. It now polls,
  as that company, each company holding an ePošťák account, each mailbox
  (credentials, firm and Peppol address) once.

[19.0.1.0.2] — 2026-10-27
-------------------------

Added
~~~~~

- Slovak and Czech translations of the user interface (``i18n/sk.po``, ``i18n/cs.po``).

[19.0.1.0.1] — 2026-10-01
-------------------------

Changed
~~~~~~~

- **Rewrote the ePošťák Firm ID help, which was correct but unactionable.** It
  opened "Only for integrator keys (sk_int_*)", which a direct customer reads as
  "not me" — and the secret is write-only, so they cannot check. A standalone
  customer with an ``sk_int_*`` key left the field empty on that reading and
  every call failed ``400 BAD_REQUEST``. The help now says to read *Configured
  key* in the form instead of inferring from the contract (a direct customer can
  still be issued an integrator key), names the 400 it causes, and points at
  Test Connection for the UUIDs.

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
