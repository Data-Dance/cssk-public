==============================================
CZ Financial Statements (Rozvaha / Výsledovka)
==============================================

The Czech country layer for the shared financial-statement framework
(``l10n_cssk_fs_base``). It is CE-clean: line values are summed from
``account.move.line`` by account-code prefix — the balance sheet (Rozvaha) is
cumulative as-of the report date, while the P&L (Výkaz zisku a ztráty) reports
the period movement. The module ships the full statutory line structure
required by vyhláška 500/2002 Sb. and the structured XML exports that feed the
DPPDP9 appendices and the commercial-register filing (sbírka listin).

Features
========

* Full statutory line structure per vyhláška 500/2002 Sb.: Rozvaha (plný-rozsah
  groups plus the key numbered lines) and Výkaz zisku a ztráty v druhovém
  členění.
* Every account of the l10n_cz směrná účtová osnova maps to exactly one leaf
  line (the partition is verified in tests), so the aggregates reconcile:
  AKTIVA = PASIVA and výsledek hospodaření = výnosy − náklady.
* The current-year result (A.V) is computed from class 5/6, so the balance
  sheet ties out even before the result is closed to účet 431.
* Přehled o peněžních tocích (cash flow, nepřímá metoda) and Přehled o změnách
  vlastního kapitálu (changes in equity) — příloha components built as a
  complete account partition into provozní/investiční/finanční činnost
  (resp. equity components), reconciling by construction (A + B + C = Δcash;
  počátek + Σ změny = konec; G = 0 asserted in tests).
* Structured XML export for every statement. There is no standalone EPO XSD for
  the full závěrka, so the XML is a structured stand-in alongside the PDF /
  commercial-register submission.

Usage
=====

Create a financial-statement record for the relevant statutory version
(Rozvaha, Výkaz zisku a ztráty, cash flow or changes in equity), set the
reporting period and compute the lines. The values are summed directly from the
posted journal items, the aggregates reconcile by construction, and the result
can be exported as structured XML for the DPPDP9 appendices and the
commercial-register filing.

Accountant note: the dlouhodobé/krátkodobé receivable & payable splits and the
opravné-položka allocations follow the standard chart convention — confirm with
a CZ accountant for entities using non-standard account assignments.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
