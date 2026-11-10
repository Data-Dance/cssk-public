F-512 from ÚDZS MU12/14/2014, bulletin1/2026
========================================

Source: https://www.udzs-sk.sk/wp-content/uploads/2026/01/VE_1_2026_sv.pdf

PDF SHA256: `d45710720fed6130842f9f99ae549e92295b7a4c0f7299d69b736cdd535008c6`

`davka601-derived-2026.xsd` is a **derived transcription**, not an independently
distributed authority XSD download. PyPDF2 2.12.1 extracts PDF pages25–44.
Pagination and the extracted XML declaration (`UTF -8`) are removed. The two
exact PDF extraction artifacts `[0 -9]` and `[A -W]` are normalized to the
visible F-512 digit/letter ranges `[0-9]` and `[A-W]`. Other schema values,
including the published trailing-space pattern after`2S`, are unchanged.

Derived SHA256: `199eb6d5c55bb442804ed869b67ab1435ff8af1ef545dfacafa41d9950dbb393`

The schema compiles, but its code-of-change pattern asks for spaces after2S.
This conflicts with the table's1–2 character code. The text format supports2S
without that schema defect; do not claim the derived XML schema accepts it.
The codec separately checks calendar dates, actual identifiers and checksums
which the published XSD's string patterns do not establish.

F-511 and F-512 specify the change date as YYYYMMDD. The generic explanation
F-514 prints DDMMYYYY; the interface tables, F-512 documentation and insurer
interface independently agree on YYYYMMDD. Text601 uses ISO8859-2; XML uses
UTF8. No lossy name transliteration is performed.
