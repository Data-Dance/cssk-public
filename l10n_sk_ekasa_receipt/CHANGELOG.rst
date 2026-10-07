=========
Changelog
=========

All notable changes to **l10n_sk_ekasa_receipt** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.0] — 2026-10-06
-------------------------

Added
~~~~~

- ``cssk.receipt.provider.sk_ekasa``: reads the QR code on a Slovak fiscal
  receipt and fetches the registered receipt — items, quantities, per-rate VAT
  recap, seller identity — from Finančná správa's document-verification service.
- Both receipt shapes: the on-line identifier (``O-``/``V-`` + 32 hex) and the
  off-line composite key (OKP, cash-register code, timestamp, number, total),
  with the service's returned identifier stored as the deduplication key.
- ``sk.ekasa.call`` ledger: every lookup recorded with its outcome, serving both
  as the hourly-budget counter and as the company's own record of what it
  verified (§ 18 ods. 11 requires truthful results be sent to Finančná správa).
- Hourly budget enforcement (default 60 per clock hour), refusing the capture
  rather than risking the IP address being blocked.
- § 18 ods. 11 gate: lookups are refused until the company declares that
  Finančná správa has been notified of the IP address it calls from. Finančná
  správa had not published the conditions of use as of 2026-10-05.
- Mapping pinned by tests against two verbatim service responses: VAT recap from
  ``vatSummary`` only (the legacy basic/reduced pair carries stale rate labels or
  no data at all), ``price`` treated as the VAT-inclusive line total,
  ``organization`` separated from ``unit``, ``icDph`` not derived from ``dic``,
  ``issueDate`` rather than ``createDate``, and a null body read as "not
  registered" rather than as an empty success.

- When a response carries no ``vatSummary``, the recap is now derived from the
  items' own rates rather than the legacy ``basic``/``reduced`` pair. The pair
  holds two rates and a receipt can carry three, so reading it would silently
  flatten a three-rate receipt; it is used only when there are no items either,
  and either path raises a warning. (From the same review.)
