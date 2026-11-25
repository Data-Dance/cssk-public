# l10n_cz_inventory_verification: developer notes

Not user documentation: this file is not rendered into a page.

## Twin of l10n_sk_inventory_verification

Same architecture (inventarizace → inventurní soupis → line, two QWeb
reports, ledger read for a dokladová inventura), different statute. The
fields follow § 29 and § 30 zákona č. 563/1991 Sb. as consolidated on
2026-01-01, not the Slovak act:

| Slovak twin | Here | Why |
|---|---|---|
| three dates on the inventarizácia (§ 30 ods. 2 písm. b) SK) | rozvahový den on the inventarizace; `datetime_start`, `datetime_end`, `rozhodny_den` on the soupis | § 30 odst. 7 písm. f)–h) are particulars of each inventura, and § 30 odst. 2 lets an inventarizace hold several. "Okamžik" is a moment, hence Datetime. |
| — | `method` | § 30 odst. 7 písm. c) |
| `counted_by_id` only | `counted_by_id` + `inventory_responsible_id` | § 30 odst. 7 písm. b) asks for two podpisové záznamy |
| — | `inventarizace_type` (periodická / průběžná), `comparison_date` | § 29 odst. 1–2; the day of valuation differs (§ 30 odst. 7 písm. d) vs e)) |
| — | `timing_warning` | § 30 odst. 6; a warning, never a constraint |
| `location`, `responsible_person_id` are statutory | kept, optional | not in § 30 odst. 7 |
| inventarizačný zápis, § 30 ods. 3 SK | internal record, cites no paragraph as its form | the Czech act prescribes none |
| closing needs `counted_by_id` | closing needs every member of `_PRESCRIBED` | § 30 odst. 7 "musí obsahovat" |

`date_start` / `date_end` on the inventarizace are computed spans of its
soupisy, kept for the list view and the window warning.

## Vybrané účetní jednotky

Vyhláška č. 270/2010 Sb. (plán inventur, inventarizační komise, dodatečný
inventurní soupis, inventarizační zpráva, inventurní zápis under § 30 odst. 8)
binds vybrané účetní jednotky only (§ 1 odst. 1 of the vyhláška; businesses
are touched by it only for cultural monuments and collections, § 1 odst. 2).
None of it is modelled here. Do not borrow its terms for the business
printouts: "inventarizační zpráva" has a defined meaning there.

## Translations

Czech-source for statutory terms and the reports; English for the chrome,
translated in `i18n/cs.po` and `i18n/sk.po`. The Slovak catalogue leaves the
Czech statutory terms alone. Regenerate the `.pot` with `odoo-bin i18n export`
before touching the `.po` files — Odoo merges a `.po` with the module's `.pot`
first, and a stale `.pot` discards entries.

## Booking of differences

The logic is in `l10n_cssk_inventory_verification_base` (three abstract
models) and shared with the Slovak twin. This module adds the concrete
`l10n.cz.inventarizacni.rozdil`, the day the entry is dated
(`_cssk_difference_date` → `comparison_date`, per soupis) and the proposed
accounts (`_cssk_counterpart_code`, `_cssk_claim_account_code`).

Where the two countries differ, on purpose:

| | SK (postupy účtovania) | CZ (ČÚS 007, vyhláška 500/2002) |
|---|---|---|
| cash schodok / schodek | 335 / 211, a receivable, no expense (§ 11 ods. 1 písm. b)) | 569 / 211 (bod 3.1, § 34) |
| own-production stock | group 61 | group 58 |
| přebytek of a depreciated asset | 384, at reálna hodnota (§ 21 ods. 2) | against the oprávky 07x / 08x (bod 3.5 písm. b)) |
| přebytek of a non-depreciated asset | 648 | group 41 (413) |
| claim on a financial asset | none: the schodok is the receivable | 378 / 668 (§ 33) |
| entry date | one day per inventarizácia | per soupis, so several entries for a průběžná |

ČÚS and the vyhláška name account groups only; the three-digit accounts are
convention. Do not "align" the tables above with each other.
