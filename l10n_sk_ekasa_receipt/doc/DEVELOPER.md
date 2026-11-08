# l10n_sk_ekasa_receipt: developer notes

Not user documentation: this file is not rendered into a page.

## What the mapping gets right

**The VAT recap is read from `vatSummary` and nowhere else.** The legacy
`vatRateBasic` / `vatRateReduced` pair was observed carrying **stale 20/10
labels** on a receipt whose items and summary said 23/5 — the amounts beside them
were right, the rates were from the pre-2025 regime — and arriving **entirely
null** on another. It also has only two slots, and three rates on one receipt is
routine in Slovak hospitality.

**`items[].price` is the VAT-inclusive line total, not a unit price.** The
twelve items on the restaurant bill sum to exactly its total, and the quantity-2
lines divide cleanly. Dividing to get a unit price loses money: 57.85 for
31.17 litres is 1.855951… and 1.86 × 31.17 is 57.98.

**Item names arrive multi-line, with modifiers already paid for.** `HOVÄDZÍ BBQ
SET\n1x Príloha navyše +3EUR` is one line of 48.00 that already contains the
3.00. The name is flattened for a label and never split.

**`organization` is the seller; `unit` is the premises.** A motorway service
station is not Vzorová čerpacia stanica's registered seat, so the premises becomes a note and
never reaches the partner record.

A receipt that is not in the system comes back as **HTTP 200 with a null body**,
never as an error, so that is tested for explicitly.
