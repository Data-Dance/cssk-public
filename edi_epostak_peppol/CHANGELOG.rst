=========
Changelog
=========

All notable changes to **edi_epostak_peppol** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-08-22
-------------------------

- Initial release. Implements the two ``edi_base_peppol`` transport hooks
  against ePošťák: ``_peppol_provider`` and ``_peppol_send``.
- Adds a **Peppol Transport** setting so a deployment with several Peppol
  transports installed picks the active one explicitly instead of inheriting
  module load order. Dispatch routes on the provider stamped on the message,
  so in-flight documents are unaffected by a later change of the setting.

- *Live-validated* 2026-08-22 against the ePošťák sandbox
  (``dev.epostak.sk``) from a throwaway Odoo 19 database: token mint, send,
  delivery-status promotion ``sent`` → ``done``, inbound poll, vendor-bill and
  credit-note import, acknowledge, and duplicate suppression on re-poll. 27
  unit tests green.
