from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_vehicle_cap_amount = fields.Monetary(
        string="Tax Vehicle Depreciation Cap",
        help="Capped depreciable base for passenger vehicles flagged on the asset "
        "(CZ §30e: 2 000 000 CZK for category M1; SK §17(34): 48 000 EUR). Leave "
        "at 0 for no cap. Set per company in its own currency.",
    )
    # Deferred-tax (odložená daň) posting from the reconciliation
    tax_deferred_journal_id = fields.Many2one(
        "account.journal", string="Deferred Tax Journal",
        domain="[('type', '=', 'general'), ('company_id', '=', id)]",
        check_company=True,
    )
    account_deferred_tax_id = fields.Many2one(
        "account.account", string="Deferred Tax Account (481)",
        check_company=True,
        help="Balance-sheet deferred-tax account (CZ/SK 481).",
    )
    account_deferred_tax_pl_id = fields.Many2one(
        "account.account", string="Deferred Tax P&L Account (592)",
        check_company=True,
        help="Profit-and-loss deferred-tax account (CZ/SK 592).",
    )

    def _cssk_asset_book_tax_difference(self, date_from, date_to):
        """Company-wide accounting (book) vs tax depreciation over a period —
        the same add-back/deduction the reconciliation wizard classifies, exposed
        as a plain method so the DPPO statement can pull it automatically.

        Returns ``{"book", "tax", "difference" (book−tax), "addback"
        (=max(diff,0), SK pripočítateľná / CZ ř.50), "deduction" (=max(−diff,0),
        odpočítateľná / ř.150)}``. Tax = the annual tax-board lines in the
        period; book = the **posted** accounting depreciation of the same assets
        over the period (``_tax_accounting_depreciation_for_period``, the same
        source the reconciliation wizard uses) — NOT the draft-inclusive
        ``book_amount`` board column, which would overstate the filing whenever
        the year's depreciation moves are not yet all posted. Zeroes if the
        tax-asset bridge isn't installed.
        """
        self.ensure_one()
        empty = {"book": 0.0, "tax": 0.0, "difference": 0.0,
                 "addback": 0.0, "deduction": 0.0}
        Line = self.env["account.asset.tax.line"]
        if "asset_id" not in Line._fields:
            return empty
        years = list(range(date_from.year, date_to.year + 1))
        lines = Line.search([
            ("company_id", "=", self.id),
            ("fiscal_year", "in", years),
        ])
        tax = sum(lines.mapped("amount"))
        book = sum(
            asset._tax_accounting_depreciation_for_period(date_from, date_to)
            for asset in lines.mapped("asset_id")
        )
        diff = book - tax
        return {
            "book": book, "tax": tax, "difference": diff,
            "addback": max(diff, 0.0), "deduction": max(-diff, 0.0),
        }
