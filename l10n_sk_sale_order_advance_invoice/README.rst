=======================================
Advance Invoices - Slovak Localization
=======================================

Slovak chart wiring for advance invoices (**preddavkové faktúry**). It connects
the country-neutral ``sale_order_advance_invoice`` module to the Slovak chart of
accounts so the advance-payment workflow posts to the correct statutory accounts.

On install it configures, for every company on the Slovak chart template (only
empty fields are filled — existing manual configuration is preserved):

* the dedicated tax-documents journal **TDADV** (Faktúry k prijatým platbám);
* the reconcilable advance-clearing account **324001** (created — the standard
  chart has no reconcilable clearing account);
* the short-term received-advance account **324000** (Prijaté preddavky);
* the long-term received-advance account **475000** (Dlhodobé prijaté preddavky).

Features
========

* Post-init hook wires the advance-invoice journal and accounts to the Slovak
  chart per company.
* Creates the reconcilable clearing account 324001 the standard SK chart lacks.
* Idempotent: only empty configuration fields are filled, so manual setup is
  preserved.

Usage
=====

Install the module on a database with the Slovak chart; the wiring runs
automatically. The advance-invoice workflow (advance / proforma invoice →
payment → tax document for the received payment → final invoice with advance
deduction) then posts to the Slovak accounts. See the Documentation below for
the accounting flow and the interactive cheat sheet.

Documentation
=============

* ``docs/index.rst`` — what gets configured and the four-step Slovak accounting
  flow for received advances.
* ``CHANGELOG.md`` — release history.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
