=========================================
Fiscal Receipt Capture — Shared Framework
=========================================

Getting a **cash-register receipt** into Odoo from a photo, a QR code or an
email attachment. This module owns the document; a *provider* supplies the data.

Providers
=========

* ``l10n_sk_ekasa_receipt`` — reads the QR code on a Slovak eKasa receipt and
  fetches the registered receipt from Finančná správa, lines and all. No OCR,
  no guessing: the figures are the ones the seller reported.
* ``l10n_cssk_receipt_capture_ai`` — reads the photograph with an LLM, for every
  receipt that carries no usable code. That is every Czech receipt (EET 2.0
  mandates no receipt and prints no code), every foreign one, and any Slovak one
  whose QR is damaged.

Models
======

``cssk.receipt``
    The captured receipt: seller, date, total, source attachment, the verbatim
    provider payload, state.

``cssk.receipt.line``
    One row per item, carrying the **VAT-inclusive line total**.

``cssk.receipt.tax``
    The per-rate VAT recap — what actually gets posted.

``cssk.receipt.provider``
    The registry. A provider is a record here plus an ``AbstractModel`` named
    ``cssk.receipt.provider.<code>`` implementing ``_can_capture`` and
    ``_capture``.

Three decisions worth knowing before reading the code
=====================================================

**The VAT recap is a model, not two fields.** A receipt's own per-rate summary
is the only trustworthy figure, and it does not fit in a pair. A Slovak
restaurant bill routinely carries three rates — food 5 %, non-alcoholic drinks
19 %, alcohol 23 % — and the legacy two-slot "basic / reduced" recap that tax
authorities still emit cannot express that. Worse, it is unreliable: measured on
two real receipts, it carried **stale 20/10 rate labels** on one (while the items
and the real recap said 23/5) and arrived **entirely null** on the other.

**Line quantities are not posted as quantities.** A fuel receipt reads 31.17 l
for €57.85. At the two decimals of a price field that is €1.86 a litre, and
1.86 × 31.17 = €57.98 — thirteen cents of invented money. The document line
therefore carries quantity 1 and the line total as its price; the real quantity
lives on ``cssk.receipt.line``, where it informs without distorting.

**Nothing is created from a receipt that does not add up.** The lines must sum to
the total, and each VAT bucket's base plus tax must match the items at that rate.
A receipt that fails is parked in *Needs Review* with the discrepancy named. The
created document is then checked back against the receipt: if Odoo's computed tax
does not equal the seller's reported tax, nothing is posted. That check is what
catches an unmapped VAT rate, whose silent symptom is a receipt posted with no
VAT and a lost deduction.

Getting a receipt in
====================

**A photograph.** Every QR code on the image is decoded (``zxing-cpp``, which a
provider that needs it declares as a dependency) and offered to the providers;
the first one a provider recognises is looked up. A receipt routinely carries
more than one code — a loyalty-app link printed above the fiscal one is common —
so the first code is not necessarily the right one, and *Codes on the
photograph* says what was found, used and ignored. A code that is present but
unreadable (a dense off-line code from a thermal printer can defeat every
decoder) is reported as such, and the photograph goes to the next reader.

**The camera.** *Scan Receipt* opens Odoo's own scanner. Live video — many
frames, autofocus, the paper held flat — reads codes a still photograph will
not, and a code no provider recognises is refused with a hint about which one
to scan.

**Identifiers printed on the paper.** When the code will not decode, the same
identifiers are usually printed beside it. A reading that supplies them lets a
provider rebuild the lookup key; the authority's figures then replace the
reading — but only if its total is the photograph's.

Attempts, failures and retries
==============================

Every attempt by every provider is a ``cssk.receipt.attempt`` row: outcome,
reason, model, tokens and cost, failed calls included. A provider that cannot
run here now (switched off, not configured, its quota spent) hands the receipt
to the next; one that ran and failed stops with the reason, stored on the
receipt and shown — never only in a log. A transient failure (a busy model, a
network error) is retried on a schedule of 15 minutes, 1 hour and 4 hours; a
refusal or an unregistered receipt is not, because the same request would get
the same answer and cost the same again.

The simplified-invoice limit
============================

A till receipt is a simplified tax document only up to a statutory amount:
**400 EUR** including VAT for a Slovak receipt (§ 74 ods. 3 písm. b) zákona
č. 222/2004 Z. z.; deduction needs a faktúra, § 51 ods. 1 písm. a)) and
**10 000 CZK** for a Czech one (§ 30 odst. 1 zákona č. 235/2004 Sb.), both
verified against the consolidated texts in force in 2026. Above it the receipt
is still a perfectly good accounting document — the purchase is booked in full —
but its VAT is not deductible from it: the vendor bill or expense carries the
gross amount with the VAT as cost and claims nothing. *Full invoice held* on
the receipt restores the deduction, and posting refuses a document that claims
VAT the receipt does not allow.

Times
=====

Receipts print local time. It is stored in UTC like every Odoo datetime, with
the receipt's own time zone beside it, and documents take the date printed on
the paper — not the UTC date, which is a day early for a receipt printed just
after midnight.

Configuration
=============

*Settings ▸ Accounting ▸ Fiscal Receipt Capture*: the purchase journal, the
default expense account, whether documents carry one line per VAT rate (the
default, which cannot drift) or one per item, and whether an unmatched seller is
created automatically.

The VAT-rate → tax mapping is shared with ``account_invoice_ai_extract`` when
that module is installed, so a database doing both invoices and receipts
configures its rates once.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
