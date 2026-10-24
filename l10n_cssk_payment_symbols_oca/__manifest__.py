# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Payment Symbols — Bank Matching (OCA)",
    "version": "19.0.1.0.0",
    "summary": "Exact variable-symbol pass in OCA's bank auto-reconciliation.",
    "description": """
CZ/SK Payment Symbols — Bank Matching (OCA)
===========================================

The Community counterpart of ``l10n_cssk_payment_symbols_ee``: statement lines
carrying a variable symbol are matched against open journal items whose
document has the same symbol, in OCA ``account_reconcile_oca``'s
auto-reconciliation, BEFORE its own invoice matching runs.

Why a dedicated pass: OCA matches an invoice when the statement line's label
is *contained in* the invoice's reference or number. A Czech or Slovak payer
quotes the variable symbol, often only in the structured reference
(``/VS2026001/SS/KS``), and the label is free text, so that test almost never
holds — and when the label is short it can hold for the wrong document.

The comparison is the one the Enterprise bridge uses, shared from
``l10n_cssk_payment_symbols``: leading-zero tolerant, bails out when several
documents carry the symbol and none matches the amount. A partial payment is
matched and leaves the rest open; an over-payment is proposed in the widget,
never reconciled automatically.

Auto-installs when both ``l10n_cssk_payment_symbols`` and
``account_reconcile_oca`` are present.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_payment_symbols", "account_reconcile_oca"],
    "auto_install": True,
    "installable": True,
}
