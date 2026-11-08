# l10n_sk_single_entry_closing: developer notes

Not user documentation: this file is not rendered into a page.

## Schema and rows

- **Príjmy and výdavky neovplyvňujúce základ dane are not on Úč FO 1-01.**
  § 4 ods. 6 f)/g) makes them their own prehľady of the denník; a vklad
  podnikateľa or a loan instalment shows up only in Úč FO 2-01's balances. A test
  asserts no PN*/VN*/C1 category is named on the form.
* **Odpisy ARE on it**, in r. 10 Ostatné výdavky, because § 4 ods. 9 puts them
  there together with kurzové rozdiely, zostatková cena predaného majetku and
  tvorba rezerv. The first draft of this module excluded non-cash rows on the
  reasoning that a statement of money cannot hold an odpis; the opatrenie says
  otherwise. (Until 19.0.1.0.3 the row named Z1/Z2 but the computation still
  dropped every non-cash row of the denník, so r. 10 never held an odpis.)
* **Rows match 3-digit synthetics, not 6-digit accounts.** A six-digit token
  matches only codes starting with it, so `221000` reported zero for a company
  whose bank account is `221100` — measured on a fresh SK chart.
* **Maturity is not in the account code.** The vysvetlivky put long-term deposits
  and loans in r. 03; those stay where their synthetic puts them (r. 11, r. 08)
  and are moved by a manual override, which records who decided.
* **Whole euros**, as the tlačivo's own heading says, with an absent figure
  emitted as an empty element rather than a zero.
* **The podpisový záznam is absent from the XML** on the vysvetlivky's own
  instruction: it is given in paper form only.

`form.300.sk.xsd`, pinned in `data/SCHEMA_VERSION` by size and md5 — it
stamps itself with a vintage (`UzFo_2014`) and nothing else, so a revision in
place would not move any value in the file. It is **not** published under
`ekr.financnasprava.sk/Formulare/XSD/` like every other schema here; it is
served beside the eForm, which names it itself. It earned its keep immediately:
it rejected a `riadok1`/`riadok2` guess in the header, where the real
structure is two repeated `riadok` elements.
