=========
Changelog
=========

All notable changes to **l10n_cssk_payment_symbols** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.2.0] — 2026-09-02
-------------------------

Fixed
~~~~~

- **Core's ``payment_reference`` is relabelled, and the symbols now appear on
  customer invoices too.** Odoo's own cs_CZ catalogue renders
  ``payment_reference`` as "Variabilní symbol", so a Czech user saw a free-text
  field labelled as the variable symbol while the real one — digits-only and
  length-checked — sat beside it. Typing the VS into the wrong box produces a
  payment the recipient cannot match, and nothing warned.

  ``payment_reference`` appears twice in ``account.view_move_form`` and the
  module's unqualified spec silently took the first, so the symbols were placed
  only beside the vendor-bill copy and customer invoices — where a Czech VS
  matters most, being what the customer is asked to quote — had none. Both
  occurrences are now pinned by their ``@invisible`` condition, which is not a
  translated attribute and so is valid as a selector, and which fails loudly if
  core reorders them.

  Carried over from 18.0, where the work was done, with 19.0's own conditions:
  core dropped ``out_receipt`` from the vendor-bill branch between the versions,
  so 18.0's selectors would have matched nothing here.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.0] — 2026-07-18
-------------------------

Added
~~~~~

- VS/KS/SS fields on ``account.payment`` (``l10n_cssk_*``, editable,
  digits-validated) — prefilled by the Register Payment wizard from the paid
  document(s) when every covered document agrees on the symbol, left empty
  otherwise. Shown on the payment form.

[19.0.1.0.0] — 2026-07-14
-------------------------

Added
~~~~~

- Initial release. Canonical VS/KS/SS fields on ``account.move`` (moved here
  from ``l10n_cssk_core``) with digits-only validation (10/4/10), variable
  symbol capped at the last 10 digits, company policy for credit-note VS
  (own number — default — or the reversed invoice's symbol), company default
  constant symbol on customer documents.
- Optional company toggle **Payment Reference = Variable Symbol** — customer
  documents then carry the VS in ``payment_reference`` on posting.
- ``variable_symbol`` / ``constant_symbol`` / ``specific_symbol`` on bank
  statement lines, populated on create from explicit values, connector
  ``transaction_details`` (incl. the ``variable_code`` key of upstream
  odoo/odoo#275611) or ``VS:``-style label tokens; the VS is prefixed into
  ``payment_ref`` (never twice) so stock matching heuristics see it.
- Invoice symbols travel to the QR generation stack via the
  ``cssk_payment_symbols`` context key.
