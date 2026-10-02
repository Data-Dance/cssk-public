=========================================================
Slovakia — Účtovná závierka v jednoduchom účtovníctve
=========================================================

The closing a SZČO keeping **jednoduché účtovníctvo** files: **UZFOv14**, one
document holding *Výkaz o príjmoch a výdavkoch Úč FO 1-01* and *Výkaz o majetku
a záväzkoch Úč FO 2-01*.

Who this is for, and who it is not
==================================

A natural person who proves their expenses is an účtovná jednotka (ZoÚ § 1
ods. 1 písm. a) bod 3) **unless they keep daňová evidencia** under § 6 ods. 11
ZDP — that exception is written into the accounting act itself. So:

* **jednoduché účtovníctvo** → files this závierka, into the register účtovných
  závierok via the FS portal (§ 23 ods. 2, § 23b ods. 1), by the income-tax
  return deadline (opatrenie § 22 ods. 3);
* **daňová evidencia or paušálne výdavky** → not an účtovná jednotka, files no
  závierka at all.

There is no micro variant: *mikro účtovná jednotka* is a podvojné concept with
its own form, and JÚ has exactly one vzor for every size.

What it is built on
===================

``l10n_cssk_fs_base``, so the states, the comparison period, manual overrides
with an audit trail, the unmapped-amount check and the XSD-validated export are
the same machinery as the Súvaha and VZS. Two things are specific:

* **Úč FO 1-01 reads the peňažný denník**, through a line kind
  ``cash_categories`` whose formula names denník category codes. § 22 ods. 1
  says the závierka is compiled "z údajov peňažného denníka, knihy pohľadávok,
  knihy záväzkov, pomocných kníh", and the vysvetlivky say the rows carry "údaje
  z príslušných prehľadov peňažného denníka" — § 4 ods. 6 d) 1–3 are rows 01–03
  and e) 1–6 are rows 05–10, one to one. Rebuilding the cash basis from account
  balances instead would mean a second implementation of it.
* **Úč FO 2-01 reads the ledger** as of the period end, by account code.

Decisions worth knowing
=======================

* **Príjmy and výdavky neovplyvňujúce základ dane are not on Úč FO 1-01.**
  § 4 ods. 6 f)/g) makes them their own prehľady of the denník; a vklad
  podnikateľa or a loan instalment shows up only in Úč FO 2-01's balances. A test
  asserts no PN*/VN*/C1 category is named on the form.
* **Odpisy ARE on it**, in r. 10 Ostatné výdavky, because § 4 ods. 9 puts them
  there together with kurzové rozdiely, zostatková cena predaného majetku and
  tvorba rezerv. The first draft of this module excluded non-cash rows on the
  reasoning that a statement of money cannot hold an odpis; the opatrenie says
  otherwise.
* **Rows match 3-digit synthetics, not 6-digit accounts.** A six-digit token
  matches only codes starting with it, so ``221000`` reported zero for a company
  whose bank account is ``221100`` — measured on a fresh SK chart.
* **Maturity is not in the account code.** The vysvetlivky put long-term deposits
  and loans in r. 03; those stay where their synthetic puts them (r. 11, r. 08)
  and are moved by a manual override, which records who decided.
* **Whole euros**, as the tlačivo's own heading says, with an absent figure
  emitted as an empty element rather than a zero.
* **The podpisový záznam is absent from the XML** on the vysvetlivky's own
  instruction: it is given in paper form only.

The schema
==========

``form.300.sk.xsd``, pinned in ``data/SCHEMA_VERSION`` by size and md5 — it
stamps itself with a vintage (``UzFo_2014``) and nothing else, so a revision in
place would not move any value in the file. It is **not** published under
``ekr.financnasprava.sk/Formulare/XSD/`` like every other schema here; it is
served beside the eForm, which names it itself. It earned its keep immediately:
it rejected a ``riadok1``/``riadok2`` guess in the header, where the real
structure is two repeated ``riadok`` elements.

Status
======

**Functional, tested live on Community 19.0** (18 tests: the row inventory
against the tlačivo, the schema digest, the denník-fed income rows with the
eForm's own totals, the exclusion of the neovplyvňujúce columns, odpisy in
r. 10, assets against liabilities, an overdrawn account reported as an úver,
whole-euro output, the empty preceding-period columns of a first závierka, the
export validating against the published schema, a nested aggregate that must not
read a stale zero, and a static partition of the chart across the rows).

**Not built:** submission to the FS portal itself (the file is produced and
validated; delivery goes through the existing submission machinery), and the
first-závierka flag is a guess from whether the books reach back before the
period, editable by the filer, because "kept podvojné účtovníctvo last year"
cannot be derived from the ledger.

Credits
=======

Data Dance s.r.o. — https://www.datadance.eu
