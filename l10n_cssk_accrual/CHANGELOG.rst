=========
Changelog
=========

All notable changes to **l10n_cssk_accrual** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.2] — 2026-07-04
-------------------------

Added
~~~~~

- CZ/SK **estimated accruals** (dohadné položky) — items where the obligation
  exists but the exact amount is not yet known (distinct from časové rozlíšenie
  deferrals, and shipped by neither Odoo CE nor EE).
- ``cssk.accrual.estimate`` with the **link & true-up** workflow: book an estimate
  at period end (estimated payable Dr expense / Cr accrual — CZ 389, SK 326;
  estimated receivable Dr accrual CZ 388 / Cr income), then link the actual
  invoice — the estimate is reversed at the invoice date and reconciled against
  the accrual account, so only the difference remains and the accrual clears.
- Accounts and journal chosen per estimate (no hard-coded chart), so it works for
  the Czech, Slovak and any custom chart.
- CE-clean (Odoo core ``account`` + ``l10n_cssk_core``).

[2026-06-30] — i18n sweep & baseline
------------------------------------

Added
~~~~~

- Full cs_CZ + sk_SK translations (Odoo 19 jsonb).
