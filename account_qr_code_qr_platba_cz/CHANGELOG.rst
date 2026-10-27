=========
Changelog
=========

All notable changes to **account_qr_code_qr_platba_cz** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0
~~~~~~~~~~~~~~~~~~

- 19.0.1.1.2 (2026-10-27) is owed to 18.0: ``*`` / ``%`` escaping in ``MSG``
  and ``RN``. The module exists on ``origin/18.0``.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.3] — 2026-10-27
-------------------------

Added
~~~~~

- Czech translation.

Fixed
~~~~~

- The tests' bank account is created with sufficient rights; their setUpClass
  failed, so they had not run.

[19.0.1.1.2] — 2026-10-27
-------------------------

Fixed
~~~~~

- **An asterisk in the payment reference broke the code.** ``*`` ends an SPD
  field, so a reference or account holder name containing one shifted every
  following field. ``MSG`` and ``RN`` now carry it as ``%2A`` (and ``%`` as
  ``%25``), as the QR Platba format specifies.

[19.0.1.1.1] — 2026-09-09
-------------------------

Changed
~~~~~~~

- Registers at sequence **15** instead of 20, so it is evaluated before PAY by
  square, payme and core's SEPA ``sct_qr``. ``_build_qr_code_vals`` takes the
  first *eligible* method, and PAY by square is eligible on any EUR SEPA IBAN
  without consulting the debtor — so with every method tied at 20 the winner was
  decided by module load order, and a Czech customer of a Slovak company was
  handed a Slovak code. Going first costs the other methods nothing: this one
  gates itself on ``currency == CZK or debtor_partner.country_code == "CZ"``, so
  everyone else falls straight through to the next candidate.

[19.0.1.1.0] — 2026-07-14
-------------------------

Added
~~~~~

- Emits ``X-VS`` / ``X-SS`` / ``X-KS`` when the invoice provides its payment
  symbols (via ``l10n_cssk_payment_symbols`` context); ``RF:`` prefers the
  variable symbol over digits-of-communication.

Fixed
~~~~~

- Guard against a missing communication string (forward-ported from 18.0).

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Czech **QR Platba** (credit-transfer) payment QR code as a ``res.partner.bank`` QR
  method, rendered on reports via the shared frame provider.
- Builds the Short Payment Descriptor string (``SPD*1.0*...``, CBA standard 1.2):
  account (ACC), amount (AM), currency (CC), message (MSG) and reference (RF),
  with VS/KS/SS carried as ``X-`` fields.
