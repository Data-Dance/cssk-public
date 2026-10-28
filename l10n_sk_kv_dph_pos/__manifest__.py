{
    "name": "Slovakia — KV DPH D.1 from Point of Sale",
    "version": "19.0.1.0.0",
    "summary": "Reports the sales of Point of Sale sessions in oddiel D.1 of "
               "the Slovak kontrolný výkaz DPH (eKasa turnover) instead of D.2.",
    "description": """
Slovakia — KV DPH D.1 from Point of Sale
========================================

A point-of-sale sale in Slovakia is recorded by a pokladnica e-kasa klient
(an ERP, or the Finančná správa's VRP), and the kontrolný výkaz DPH reports
that turnover in oddiel **D.1**, not D.2. Without this bridge the closing entry
of a POS session reached D.1 only if its journal was marked ``D.1`` by hand.

The closing entry of a ``pos.session`` is recognised as eKasa turnover; an
invoiced POS order stays an invoice (A.1 / D.2), as the poučenie asks.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_sk_kv_dph", "point_of_sale"],
    "auto_install": True,
    "installable": True,
}
