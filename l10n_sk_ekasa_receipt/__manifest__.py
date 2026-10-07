# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovak eKasa Receipt Capture (bločky z QR kódu)",
    "version": "19.0.1.0.0",
    "summary": "Read the QR code on a Slovak fiscal receipt and fetch the "
               "registered receipt — items, quantities and the VAT recap — "
               "from Finančná správa's document-verification service.",
    "description": """
Slovak eKasa Receipt Capture
============================

A Slovak fiscal receipt carries a QR code, and behind it Finančná správa holds
the receipt the seller actually registered: every item, its quantity, its VAT
rate, and the per-rate VAT recap. This module reads the code and fetches that
record, so a bloček is posted from the seller's own figures rather than from an
OCR guess.

Both receipt shapes are handled:

* **On-line** — the QR code *is* the identifier (``O-`` + 32 hex, or ``V-`` for
  a VRP receipt) and nothing else, so the lookup is unavoidable.
* **Off-line** — printed when the till exceeded the response-time limit, with no
  identifier. The QR instead carries
  ``OKP:kódPokladnice:dátumČas:poradovéČíslo:celkováSuma``, which the service
  accepts as a composite key. An off-line receipt is not permanently off-line:
  once the till catches up the service returns its real identifier, which is
  what this module stores as the deduplication key.

Legal basis
-----------

Act **384/2025 Z. z. o evidencii tržieb**, in force since 1 January 2026,
creates the service outright. § 2 ai) defines the *služba na overovanie dokladov*
as the service that, through the QR code, allows one to verify the data held in
the eKasa system **and "sprístupňovať a získavať tieto údaje"**; § 2 aj) defines
an *overovateľ* as a person entitled to do so; § 18 ods. 3 obliges the seller to
tolerate the disclosure.

§ 18 ods. 11 is the duty side, and this module surfaces it rather than hiding it:
an overovateľ must **notify Finančná správa of the IP address** it will use
before first use, must send truthful verification results, and must follow
conditions Finančná správa determines and publishes. Those conditions were **not
yet published** when this module was written (checked 5 October 2026), so the
company settings carry the declaration fields and a warning, and lookups are
refused until someone states that the notification has been made.

Rate limit
----------

The service allows roughly **60 receipts per clock hour per IP address**. This
module counts its own calls per company and per hour and refuses to exceed the
budget rather than getting the address blocked. That budget is per *address*, not
per company, which is the argument for eventually moving the call into the
accountant's browser: each user then has their own.

Configuration
-------------

*Settings ▸ Accounting ▸ Fiscal Receipt Capture ▸ Slovak eKasa*: enable the
lookup, declare the notified IP address and the date it was notified, and
optionally lower the hourly budget.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_receipt_capture"],
    "external_dependencies": {"python": ["requests"]},
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/cssk_receipt_provider.xml",
        "views/sk_ekasa_call_views.xml",
        "views/cssk_receipt_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
