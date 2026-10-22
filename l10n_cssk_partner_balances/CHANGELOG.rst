=========
Changelog
=========

All notable changes to **l10n_cssk_partner_balances** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-07-04
-------------------------

Fixed
~~~~~

- Wave 2 partner-balance correctness: the open-AR/AP snapshot and the netting
  auto-allocation / reconciliation were tightened for accuracy.
- Form-load performance: open-balance reconciliation resolved via ``_read_group``
  instead of an N-per-line query fan-out (down to ≤3 queries).

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Slovak/Czech **saldokonto** — ``cssk.partner.confirmation`` (mail.thread) +
  ``cssk.partner.confirmation.line``: a stored, reproducible snapshot of a
  partner's open receivables and payables as of a date, a state machine
  (draft → sent → agreed / disputed), a bilingual SK/EN countersign PDF, a bulk
  issue wizard, and disputed lines that can be blocked (excluded from totals,
  still shown on the PDF).
- **Mutual offsetting (zápočet)** — ``cssk.partner.netting.agreement`` with picker
  wizard: auto-allocates the offset up to ``min(receivables, payables)``, on
  posting builds a clearing entry (credit AR / debit AP) and reconciles the
  offset invoices (partial offsetting supported), undo via cancel-with-reversal,
  ``ZAP/YYYY/NNNN`` sequence. Two legal modes: bilateral (countersigned before
  effect) and unilateral (effective on delivery, no countersignature), the PDF
  switching wording between them.
- CE-clean (Odoo core ``account`` + ``mail``); complements OCA ``partner_statement``.
  Full cs_CZ + sk_SK translations.
