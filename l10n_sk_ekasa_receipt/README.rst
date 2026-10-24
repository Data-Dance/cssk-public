============================================
Slovak eKasa Receipt Capture (bločky z QR)
============================================

A Slovak fiscal receipt carries a QR code, and behind it Finančná správa holds
the receipt the seller actually registered: every item with its quantity and VAT
rate, and the per-rate VAT recap. This module reads the code and fetches that
record, so a bloček is posted from the seller's own figures instead of an OCR
guess.

The two receipt shapes
======================

**On-line.** The QR code *is* the identifier — ``O-`` and 32 hexadecimal
characters, or ``V-`` from the virtual register — and carries nothing else, so
the lookup is not an optimisation, it is the only way to learn anything.

**Off-line.** Printed when the till exceeded the response-time limit, with no
identifier assigned yet. The QR instead carries
``OKP:kódPokladnice:dátumČas:poradovéČíslo:celkováSuma``, which the service takes
as a composite key. An off-line receipt is **not permanently off-line**: once the
till catches up the service returns its real identifier, and that is what this
module stores as the deduplication key — the same purchase otherwise has two
possible QR payloads and only one identity.

Legal basis, and the duty that comes with it
============================================

Act **384/2025 Z. z. o evidencii tržieb**, in force since 1 January 2026,
creates the service outright. Before it, Finančná správa's standing answer was
that the *Over doklad* API could not be made available to third parties at all.

* § 2 ai) — the *služba na overovanie dokladov* lets one verify the data held in
  the eKasa system through the receipt's QR code **and "sprístupňovať a získavať
  tieto údaje"**.
* § 2 aj) — an *overovateľ* is a person entitled to do so under § 18 ods. 11.
* § 18 ods. 3 — the seller **"je povinný strpieť"** the disclosure.
* § 18 ods. 11 — before first use the overovateľ must **notify Finančná správa
  of the IP address** it will call from, must send truthful verification results,
  and must follow conditions Finančná správa determines and publishes.

**Those conditions were not published when this module was written** (checked
5 October 2026). The module therefore does not pretend the obligation away: the
company settings carry the declaration, and every lookup is refused until
somebody states that the notification has been made. Satisfying it today means
writing to Finančná správa.

Photographs and the printed identifiers
=======================================

The QR code is read off the photograph (``zxing-cpp``, a dependency of this
module), so a photographed receipt is looked up — not read by a model. A
loyalty-app QR printed above the fiscal one is ignored: only a code this module
can parse is used.

When the code will not decode, the identifiers printed beside it are used
instead: ``UID:`` on an on-line receipt; on an off-line one the OKP, the
cash-register code, the date and time, the number and the total. Two things
make that work in practice. The receipt prints the identifier in a font where
the letter **O** and the digit **0** look alike, and an identifier never starts
with zero, so a printed ``0-`` is read as ``O-``. And a till may print its number
as ``202609/5`` where eKasa holds ``5``: the part after the last slash is tried
first. A misread key finds no receipt rather than a wrong one, and the
service's total must match the photograph's in any case.

The printed time is Bratislava time whoever captures the receipt and wherever
their browser is.

Rate limit
==========

The service permits roughly **60 lookups per clock hour per IP address** and
blocks the address beyond that. This module keeps its own ledger
(``sk.ekasa.call``) and refuses to exceed the configured budget rather than lose
access. Note that the real limit is per *address*: several companies behind one
egress address share one budget, which is the argument for eventually moving the
call into the accountant's browser — the service sends
``Access-Control-Allow-Origin: *``, so that is possible without a proxy, and each
user would then have their own budget and their own notified address.

What the mapping gets right on purpose
======================================

Each of these was measured on a real receipt, and each is a way to post the wrong
number:

**The VAT recap is read from ``vatSummary`` and nowhere else.** The legacy
``vatRateBasic`` / ``vatRateReduced`` pair was observed carrying **stale 20/10
labels** on a receipt whose items and summary said 23/5 — the amounts beside them
were right, the rates were from the pre-2025 regime — and arriving **entirely
null** on another. It also has only two slots, and three rates on one receipt is
routine in Slovak hospitality.

**``items[].price`` is the VAT-inclusive line total, not a unit price.** The
twelve items on the restaurant bill sum to exactly its total, and the quantity-2
lines divide cleanly. Dividing to get a unit price loses money: 57.85 for
31.17 litres is 1.855951… and 1.86 × 31.17 is 57.98.

**Item names arrive multi-line, with modifiers already paid for.** ``HOVÄDZÍ BBQ
SET\n1x Príloha navyše +3EUR`` is one line of 48.00 that already contains the
3.00. The name is flattened for a label and never split.

**``organization`` is the seller; ``unit`` is the premises.** A motorway service
station is not Vzorová čerpacia stanica's registered seat, so the premises becomes a note and
never reaches the partner record.

**``icDph`` is not ``"SK" + dic``.** A VAT-group member files under the group's
number: on one receipt ``dic`` is 2077000002 while ``icDph`` is SK7199000006.
Both are stored; neither is derived.

**``issueDate``, not ``createDate``** — they differ, and the issue date is the
accounting date. And ``okp`` comes back in either case, so it is stored
upper-cased.

A receipt that is not in the system comes back as **HTTP 200 with a null body**,
never as an error, so that is tested for explicitly.

Configuration
=============

*Settings ▸ Accounting ▸ Fiscal Receipt Capture ▸ Slovak eKasa*.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
