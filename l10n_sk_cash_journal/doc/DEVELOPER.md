# l10n_sk_cash_journal: developer notes

Not user documentation: this file is not rendered into a page.

## Tests that pin the CZ/SK difference

- **Poistné podnikateľa is a daňový výdavok** (§ 19 ods. 3 písm. i ZDP). The
  Czech module files the same payment as non-deductible, and a test in each
  module asserts the disagreement so nobody "harmonises" them.
* **Jednoduché účtovníctvo is still open to a Slovak SZČO** (ZoÚ § 9 ods. 2
  písm. a), in the 2026 and the 2027 wording. It was closed to Czech OSVČ. The
  company regime field offers `ju` only outside Czechia.
