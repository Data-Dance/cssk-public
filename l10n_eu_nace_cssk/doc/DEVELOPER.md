# l10n_eu_nace_cssk: developer notes

Not user documentation: this file is not rendered into a page.

## Refreshing the data

The CZ subclasses come from the Czech Statistical Office's codelist CZ-NACE 2025
(`kodcis` 80143, open data), exported 2026-09-29 to
`data/cz_nace_2025_subclasses.csv` (716 rows, md5
`f1263818cdc809fee6a0228b580eae7d`). Refresh: download levels 5 of
`https://apl2.czso.cz/iSMS/do_cis_export?kodcis=80143&typdat=0&cisjaz=203&format=2&separator=%2C`
(Czech) and `cisjaz=8260` (English).
