# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Intrastat in the statutory footprint (CZ/SK)",
    "summary": "A document says which Intrastat declaration reports it, "
               "alongside the VAT return, control statement and financial "
               "statements it feeds.",
    "description": """
Intrastat in the statutory footprint
====================================

The reverse drill answers "which statutory rows does this posting feed", and
Intrastat was the one reportable obligation it never mentioned. A document that
moves goods across an EU border can be reported on a VAT return, a súhrnný
výkaz AND an Intrastat declaration, and until now the drill named the first two
and stayed silent about the third — which reads as "no Intrastat obligation
here" rather than as "not implemented".

**Movement-driven, not account-driven.** Every other contributor answers from
the account code or a tax tag. Intrastat answers from neither: what puts a line
on a declaration is the goods crossing a border, and the declaration itself
records which lines it took. So this reads the link the declaration already
stores (``intrastat.product.computation.line.invoice_line_id``) rather than
re-deriving eligibility — the same principle that keeps the control-statement
and EC-sales contributors from drifting: read what the forward direction
stored, never re-decide it.

Bridge module. The renderer ``l10n_cssk_intrastat_base`` depends on ``base``
alone, deliberately, so that the CE (OCA) and EE adapters can share it; and
neither country adapter depends on ``l10n_cssk_core``, where the footprint hook
lives. This glue therefore belongs in neither and installs itself when both
sides are present.

When it appears: Odoo installs an ``auto_install`` module when a dependency
TRANSITIONS to "to install", not merely when both are already installed. So it
arrives with the Intrastat module on a database that already has the CZ/SK
localization, and on a database where both were installed before this module
existed it has to be installed once by hand. That is Odoo's rule for every
auto-install bridge, not a property of this one.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_core",
        "intrastat_product",
    ],
    "auto_install": True,
    "installable": True,
}
