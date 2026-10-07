# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fiscal Receipt Capture — Shared Framework",
    "version": "19.0.1.0.0",
    "summary": "Country-neutral framework for capturing cash-register receipts "
               "(bločky / účtenky) into Odoo: a provider registry, the captured "
               "receipt with its lines and authoritative VAT recap, "
               "reconciliation gates, and a vendor-bill sink.",
    "description": """
Fiscal Receipt Capture — Shared Framework
=========================================

The country-neutral substrate for getting a **cash-register receipt** into Odoo
from a photo, a QR code or an email attachment.

It owns the document, not the acquisition. A *provider* supplies the data:

* ``l10n_sk_ekasa_receipt`` — reads the QR code on a Slovak eKasa receipt and
  fetches the registered receipt, lines and all, from Finančná správa.
* ``l10n_cssk_receipt_capture_ai`` — reads the photo with an LLM, for receipts
  that carry no usable code (every Czech receipt, every foreign one, and any
  Slovak one whose QR is damaged).

Provides
--------

* ``cssk.receipt`` (``mail.thread``) — the captured receipt: seller, date,
  total, source attachment, raw provider payload, state.
* ``cssk.receipt.line`` — one row per receipt item, carrying the **VAT-inclusive
  line total** as the authoritative figure.
* ``cssk.receipt.tax`` — the per-rate VAT recap, which is what actually gets
  posted. Never derived from the lines when the provider supplies it.
* ``cssk.receipt.provider`` — the provider registry; each provider ships a
  record plus an ``AbstractModel`` named ``cssk.receipt.provider.<code>``.
* A **vendor-bill sink** (``account.move``), with the expense sink in
  ``l10n_cssk_receipt_capture_expense``.

Why the VAT recap is a separate model
-------------------------------------

Because a receipt's own summary is the only trustworthy source and it does not
fit in two fields. A Slovak restaurant bill routinely carries **three** rates
(food 5 %, non-alcoholic drinks 19 %, alcohol 23 %), and the legacy two-slot
"basic / reduced" recap that tax authorities still emit cannot express that —
when it is present at all.

Why line quantities are not posted as quantities
------------------------------------------------

Because ``price_unit × quantity`` would not foot. A fuel receipt reads 31.17 l
for €57.85; at Odoo's two-decimal price precision that is €1.86 a litre, and
1.86 × 31.17 = €57.98 — thirteen cents of invented money. The document line
therefore carries quantity 1 and the line total as its price, with the real
quantity and unit kept on ``cssk.receipt.line`` where they inform without
distorting.

Reconciliation gates
--------------------

Nothing is created from a receipt that does not add up: the lines must sum to
the total, and each VAT bucket's base plus tax must match the lines assigned to
that rate. A receipt that fails is parked in *Needs Review* with the discrepancy
named, never silently rounded into place.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/cssk_receipt_provider_views.xml",
        "views/cssk_receipt_views.xml",
        "views/res_config_settings_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}
