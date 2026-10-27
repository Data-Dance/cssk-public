==============================================
CZ Financial Statements (Rozvaha / Výsledovka)
==============================================

The Czech country layer for the shared financial-statement framework
(``l10n_cssk_fs_base``). It is CE-clean: line values are summed from
``account.move.line`` by account-code prefix — the balance sheet (Rozvaha) is
cumulative as-of the report date, while the P&L (Výkaz zisku a ztráty) reports
the period movement. The module ships the
statement structure of vyhláška 500/2002 Sb. in the zkrácený rozsah for the
Rozvaha and most of the numbered items of the Výkaz zisku a ztráty — not the
plný rozsah — and the structured XML exports that feed the DPPDP9 appendices.

Features
========

* Line structure per vyhláška 500/2002 Sb.: the Rozvaha in the items of the
  zkrácený rozsah and the Výkaz zisku a ztráty v druhovém členění without
  V., D.2.1–D.2.2, E.1–E.3, IV.1–IV.2, V.1–V.2, VI.1–VI.2 and J.1–J.2. An
  obchodní společnost must file the VZZ in plný rozsah (§ 3a odst. 4 of the
  vyhláška), and a unit with an audit obligation both statements; complete
  the missing items outside Odoo.
* Every account of the l10n_cz směrná účtová osnova maps to exactly one leaf
  line (the partition is verified in tests), so the aggregates reconcile:
  AKTIVA = PASIVA and výsledek hospodaření = výnosy − náklady.
* The current-year result (A.V) is the period movement of class 5/6 (equal to
  the VZZ result), so the balance sheet ties out even before the result is
  closed to účet 431. Earlier years' results must be on 428/429/431 (A.IV);
  where a year was never closed, AKTIVA ≠ PASIVA by that year's result.
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
