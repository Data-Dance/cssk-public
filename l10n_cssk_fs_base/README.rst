================================================
CZ/SK Financial Statements — Shared Framework
================================================

Country-neutral engine behind the Slovak **Súvaha** / **VZS** and Czech
**Rozvaha** / **VZZ**. A hierarchical line tree computed from **account-code
balances** + aggregates, for a current and a comparison (prior) period.

**CE-clean:** reads ``account.move.line`` balances directly (by account code),
no ``account_reports``.

Architecture
============

* ``cssk.fs.statement.version`` — line defs + statement kind + template + schema.
* ``cssk.fs.statement.line.def`` — ``accounts`` (code formula; balance sheet =
  as-of, P&L = period), ``aggregate`` (formula over codes), ``manual``.
* ``cssk.fs.statement`` — computes current + prior period; per-line overrides
  preserved across recompute; XSD-validated XML export.

Status
======

**Functional core.** Account-code evaluation, comparison period and overrides
are verified by tests. To complete (country modules + next passes):

* The SK Súvaha's 3-column **Brutto / Korekcia / Netto** split (this core
  computes one net value per line).
* Full statutory line set (Súvaha ~145 lines, VZS), Poznámky, mikro variant.
* Official UZPODv14 / UZMUJv14 XSD + XML templates.
* Accountant validation of the account→line mapping.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
