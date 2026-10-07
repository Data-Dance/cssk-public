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
