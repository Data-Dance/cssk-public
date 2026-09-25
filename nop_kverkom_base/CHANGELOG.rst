=========
Changelog
=========

All notable changes to **nop_kverkom_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-09-13
-------------------------

Fixed
~~~~~

- **The chatter posted its own HTML as visible text.** ``message_post``
  ESCAPES a plain ``str`` and renders only a ``markupsafe.Markup`` —
  ``mail_thread.py`` states it on the parameter and applies it at
  ``'body': escape(body)``. Nothing failed: the post succeeded and the log was
  clean, which is why it survived to a user.
- Built as ``Markup(template) % args`` rather than by wrapping the finished
  string. ``%`` on a ``Markup`` escapes what it substitutes; wrapping the join
  renders it — and the interpolated values here are not ours, so the shorter
  fix would have turned an escaping bug into an injection one.

- One site: the late-payment refund note. The IBAN comes off an inbound
  payment message, so it is escaped through ``%`` rather than trusted into
  the template.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Transport layer for Slovak QR Platby via the National Operator of Payments (NOP,
  operated by KVERKOM) for instant bank-to-bank QR payments.
- ``nop.pokladnica`` — cash-register configuration (mTLS certificate, VATSK,
  POKLADNICA id, integration vs production environment).
- ``nop.transaction`` — authoritative ledger of payment notifications received from
  the bank through NOP.
- ``NopClient`` service — mTLS-authenticated REST client wrapping
  ``generateNewTransactionId``, ``getAllTransactions``, and ``getTransactionHistory``.
- Data-integrity verification: SHA-256 hash of ``IBAN|AMOUNT|EUR|endToEndId``.
- Rate-limited polling backed by a safety cron; non-confirmation receipt report.
- No POS dependency in the transport itself — POS/invoice integrations ship as
  separate modules that depend on this one.
