from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_sk_kv_is_simplified = fields.Boolean(
        string="Simplified invoice (KV DPH B.3)",
        help="Mark received documents that are simplified invoices / receipts "
        "(zjednodušená faktúra, bloček z e-kasy). Their input VAT is reported in "
        "KV DPH section B.3 — aggregated in B.3.1 below the 3 000 EUR period "
        "threshold, or per supplier in B.3.2 at/above it.\n"
        "NB: toggling this on an already-posted move does not auto-recompute "
        "the section tag; recompute the statement (or the line) afterwards.",
    )
