# l10n_cz_dppo: developer notes

Not user documentation: this file is not rendered into a page.

## Vendored data

- `ř.10` (výsledek hospodaření před zdaněním) is computed from the P&L:
  class 6 − class 5, excluding the income-tax accounts 591–599.
* The připočitatelné / odčitatelné adjustments (ř.20–170), the § 34
  deductions (ř.230 ztráta, ř.240 pre-2005 odečty, ř.242 VaV, ř.243 odborné
  vzdělávání), the § 20 odst. 8 dary (ř.260) and the slevy na dani (ř.300)
  are manual, accountant-entered, and aggregate into the spine.
* The II. oddíl tax-calculation spine (ř.10 → ř.340) is arithmetic:
  základ daně → zaokrouhlení → daň 21 % / 19 % (§ 21 odst. 1, by the
  period's first day) → daň po slevách →
  celková daňová povinnost.
* Each spine line maps to its official EPO `VetaO/@kc_ii*` attribute; only
  non-zero spine lines are emitted.
* The export builds the EPO `Pisemnost`/`DPPDP9` XML and validates it
  against the bundled official DPPDP9 XSD (`data/dppdp9_epo2.xsd`).
* Statement types Řádné (B), Opravné (O) and Dodatečné (E) are shipped as
  version data.
* The účetní závěrka travels inside the return: link the computed
  `l10n_cz_fs` Rozvaha and Výkaz zisku a ztráty of the same period, and the
  export files them as `VetaUA` (aktiva — brutto / korekce / netto / netto
  minulé), `VetaUD` (pasiva) and `VetaUB` (VZZ druhové členění), in
  thousands, in the plný or zkrácený rozsah of the linked statements
  (vyhláška 500/2002 Sb., § 3a; both must be of the same one). Each EPO row
  takes the
  `l10n_cz_fs` row of the same statutory designation — one account mapping,
  not two. The row numbers come from the EPO číselník vendored as
  `data/uv_radky_500.csv`; `models/dppdp9_vykazy.py` maps every row of
  either rozsah or states why it is not applicable. XSD and číselník are
  pinned in `data/SCHEMA_VERSION`.
