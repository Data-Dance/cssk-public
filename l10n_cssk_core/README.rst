==================================
CZ/SK Localization — Shared Core
==================================

Country-neutral foundation for the Czech & Slovak statutory localization
(``l10n_cssk_*`` / ``l10n_sk_*`` / ``l10n_cz_*``).

Depends on **Odoo core only** (``account`` + ``mail``) — no ``account_reports``,
no OCA report engine — so it installs on Community and Enterprise, 18.0 and 19.0.

Provides
========

* ``cssk.tax.authority`` — tax-office registry (submission code for XML);
  the offices themselves are loaded by ``l10n_sk_statutory`` /
  ``l10n_cz_statutory``.
* ``cssk.person.type`` — person / entity-type catalogue.
* ``res.company`` / ``res.partner`` field extensions and the IČO check.
* A Settings block (Accounting → Settings → Czech / Slovak Localization):
  default tax authority, year-end closing journals, VAT deferral account and
  the optional Community report modules.
* ``cssk.statutory.submission.mixin`` — the life cycle shared by every
  statutory filing: export (content checks, XSD validation; non-blocking
  warnings are shown to the user), the filed copy, amendments, and the
  filed-versus-computed comparisons.

The user documentation is in ``doc/`` (English, Slovak, Czech).

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
