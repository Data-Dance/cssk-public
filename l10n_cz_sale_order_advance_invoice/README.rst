======================================
Advance Invoices - Czech Localization
======================================

Czech chart wiring for advance invoices (zálohové faktury). This app connects
the country-neutral ``sale_order_advance_invoice`` flow to the Czech chart of
accounts (``l10n_cz``) so that received advances and their tax documents post to
the statutory accounts.

On install it configures, for every company on the Czech chart template, the
dedicated tax-documents journal and the received-advance accounts. Existing
manual configuration is preserved — only empty fields are filled.

Features
========

* Creates the reconcilable advance-clearing account **324001** (Přijaté zálohy –
  zúčtování / daňový doklad) — the standard Czech chart has no reconcilable
  clearing account, so this module ships one.
* Wires the short-term received-advance account **324000** (Přijaté provozní
  zálohy) and the long-term received-advance account **475000** (Dlouhodobé
  přijaté zálohy).
* Sets up the tax-documents journal **TDADV** (Daňové doklady k přijatým
  platbám) for the tax document issued on a received payment.
* Idempotent post-install hook: only empty fields are filled, so manual
  configuration is never overwritten.

Usage
=====

Install the module on a company already on the Czech chart (``l10n_cz``). The
post-install hook wires the journal and accounts automatically; no manual
configuration is required. The advance-invoice workflow itself is provided by
``sale_order_advance_invoice``:

1. **Zálohová (proforma) faktura** — a request for payment; not posted.
2. **Received payment** — bank 221 against the clearing account 324001.
3. **Daňový doklad k přijaté platbě** (tax document for the received payment,
   within 15 days) — 324001 / 324000 (base) + 343 (VAT); the clearing account is
   reconciled against the payment and returns to zero.
4. **Final invoice** — the full supply (311 / 604 + 343) with deduction of the
   advance and reversal of the VAT already declared on the advance.

Documentation
=============

* ``docs/index.rst`` — Czech account-wiring reference (accounts, journal and the
  accounting flow).
* ``CHANGELOG.md`` — release history.
* The interactive cheat sheet for the underlying flow lives in
  ``sale_order_advance_invoice/static/description/``.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
