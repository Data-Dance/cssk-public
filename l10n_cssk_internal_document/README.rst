====================
CZ/SK Interní doklad
====================

Prints a journal entry as an **interní doklad** (CZ) or **interný doklad** (SK):
the accounting document for an entry that has no external document behind it,
such as an accrual, depreciation, revaluation, a closing entry or a manual correction.

Czech § 11 odst. 1 zákona č. 563/1991 Sb., o účetnictví, and Slovak § 10 ods. 1
zákona č. 431/2002 Z. z. require the same things of an accounting document. The
printout carries each of them:

* označení dokladu: the entry's number;
* obsah účetního případu: the reference, else the note, else the line labels;
* účastníci: the company and every partner on the entry;
* peněžní částka: the entry's total;
* datum vyhotovení: the day the entry was created;
* datum uskutečnění účetního případu: the accounting date;
* the lines, with account, label, partner, analytics, Má dáti / Dal;
* podpisový záznam of the person responsible for the case (the entry's creator)
  and of the person responsible for booking it (whoever posted it). Each has a
  line to sign on.

A draft is marked NEZAÚČTOVÁNO / NEZAÚČTOVANÉ.

The wording is the statute's own. It is chosen by the company's fiscal country (SK
Slovak, otherwise Czech) and is not translated.

Print it from a journal entry: *Print → Interní / interný doklad*. OCA's
``account_move_print`` is a generic "Journal Entry" printout and can be installed
alongside.
