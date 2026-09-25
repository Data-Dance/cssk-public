from odoo import fields, models


class AccountAssetBookTaxReport(models.Model):
    """Book-vs-tax depreciation analysis view — OCA (Community) edition.

    Concrete SQL-view model of ``account.asset.book.tax.report.mixin`` (see the
    core module for the shared query): the OCA book side is the asset's
    depreciation table (``account.asset.line`` of type ``depreciate``),
    matching ``_cssk_book_depreciation_by_year()`` — every depreciation line
    counts as book depreciation, lines with a journal entry (``move_id``) feed
    ``book_amount_posted``.
    """

    _name = "account.asset.book.tax.report"
    _inherit = "account.asset.book.tax.report.mixin"
    _description = "Book vs Tax Depreciation Report"
    _auto = False
    _order = "asset_id, fiscal_year"

    asset_id = fields.Many2one("account.asset", string="Asset", readonly=True)

    def _book_sql(self):
        # ``remaining_value`` decreases along the board, so MIN() per year is
        # the year-end book residual.
        return """
    SELECT dl.asset_id,
           EXTRACT(YEAR FROM dl.line_date)::int AS fiscal_year,
           SUM(dl.amount) AS book_amount,
           COALESCE(SUM(dl.amount)
                    FILTER (WHERE dl.move_id IS NOT NULL), 0.0)
               AS book_amount_posted,
           MIN(dl.remaining_value) AS book_residual
      FROM account_asset_line dl
     WHERE dl.type = 'depreciate'
       AND dl.line_date IS NOT NULL
     GROUP BY dl.asset_id, EXTRACT(YEAR FROM dl.line_date)
"""
