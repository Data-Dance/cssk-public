=========
Changelog
=========

All notable changes to **account_abo** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- The payment method is now **ABO (Czech credit transfer)**, no longer
  *Czech/Slovak*: the file accepts CZK and Czech accounts only, and the user
  guide is published in English and Czech.

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.1.0] — 2026-10-27
--------------------------

Fixed
~~~~~

- **A credit note grouped with its invoice can now be paid by file.** The
  file had one item per payment line, so the credit note became a negative
  item and the export was refused, although the order books one payment of
  the net amount. Such a group is now one item of that net amount, under the
  invoices' variable symbol (none when the netted invoices carry different
  ones). Groups without a credit note still have one item per invoice.

[19.0.2.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- A payment order whose lines carry different dates is refused rather than
  executed on the first line's date; a zero or negative line is refused rather
  than written.

[19.0.2.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Export of Czech/Slovak domestic credit transfers (úhrady, data type 1501) in the
  ABO payment-file format, generated on an OCA ``account.payment.order``
  (CE-clean — no Enterprise dependency).
- Batch (hromadný) record arrangement: the orderer account is carried in the
  group header.
- Variable / constant / specific symbol (VS / KS / SS) resolved per payment line,
  with a memo/communication fallback.
- WIN1250 encoding with ASCII fallback.
- File building delegated to the shared ``account_cz_bankfile_base`` ABO builder;
  ABO payment method registered via ``data/account_payment_method.xml``.
