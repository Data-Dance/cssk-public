from odoo import fields, models, tools

# Assembled by the *concrete* bridge report model — never executed by this core
# module on its own (the tax CTE needs ``account_asset_tax_line.asset_id`` and
# the final join needs the ``account_asset`` table, both of which only exist
# once a bridge is installed; ``init()`` below skips the abstract mixin).
#
# One row per (asset, fiscal year): the tax side aggregates the non-posted tax
# board (annual lines; §30a monthly lines collapse into their year), the book
# side comes from the edition-specific ``_book_sql()``. A FULL OUTER JOIN keeps
# years present on only one side (e.g. book depreciation running longer than
# the statutory tax life, or a suspended tax year), and
# ``difference = book − tax`` is the DPPO add-back/deduction of the year.
REPORT_QUERY_TEMPLATE = """
WITH tax AS (
    SELECT l.asset_id,
           l.fiscal_year,
           SUM(l.amount) AS tax_amount,
           MIN(l.residual) AS tax_residual,
           BOOL_AND(l.posted) AS tax_posted
      FROM account_asset_tax_line l
     WHERE l.fiscal_year IS NOT NULL
     GROUP BY l.asset_id, l.fiscal_year
),
book AS (
%(book_sql)s
)
SELECT ROW_NUMBER() OVER (
           ORDER BY COALESCE(t.asset_id, b.asset_id),
                    COALESCE(t.fiscal_year, b.fiscal_year)
       ) AS id,
       a.id AS asset_id,
       a.company_id AS company_id,
       a.tax_class_id AS tax_class_id,
       COALESCE(t.fiscal_year, b.fiscal_year) AS fiscal_year,
       COALESCE(t.tax_amount, 0.0) AS tax_amount,
       t.tax_residual AS tax_residual,
       COALESCE(t.tax_posted, FALSE) AS tax_posted,
       COALESCE(b.book_amount, 0.0) AS book_amount,
       COALESCE(b.book_amount_posted, 0.0) AS book_amount_posted,
       b.book_residual AS book_residual,
       COALESCE(b.book_amount, 0.0) - COALESCE(t.tax_amount, 0.0) AS difference
  FROM tax t
  FULL OUTER JOIN book b
       ON b.asset_id = t.asset_id AND b.fiscal_year = t.fiscal_year
  JOIN account_asset a ON a.id = COALESCE(t.asset_id, b.asset_id)
"""


class AccountAssetBookTaxReportMixin(models.AbstractModel):
    """Shared scaffolding of the book-vs-tax depreciation analysis view.

    Follows the bridge architecture of :class:`account.asset.tax.mixin`: this
    core module never references the asset model, so the *concrete*
    ``account.asset.book.tax.report`` SQL-view model — which needs ``asset_id``
    and the edition's accounting-depreciation tables — is defined by each
    bridge (``account_asset_tax_ee`` / ``account_asset_tax_oca``; the bridges
    are mutually exclusive, so the model name never clashes). A bridge only
    declares ``asset_id`` and implements :meth:`_book_sql`; the common fields,
    the tax-side aggregation and the FULL OUTER JOIN live here.
    """

    _name = "account.asset.book.tax.report.mixin"
    _description = "Book vs Tax Depreciation Report (shared)"

    company_id = fields.Many2one("res.company", readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    fiscal_year = fields.Integer(string="Fiscal Year", readonly=True)
    tax_class_id = fields.Many2one(
        "account.asset.tax.class", string="Tax Depreciation Group", readonly=True,
    )
    tax_amount = fields.Monetary(string="Tax Depreciation", readonly=True)
    tax_residual = fields.Monetary(string="Tax Residual Value", readonly=True)
    tax_posted = fields.Boolean(
        string="Filed", readonly=True,
        help="Every tax-depreciation line of the year has been filed (frozen).",
    )
    book_amount = fields.Monetary(string="Book Depreciation", readonly=True)
    book_amount_posted = fields.Monetary(
        string="Book Depreciation (Posted)", readonly=True,
        help="Only the book depreciation whose journal entry is posted — the "
        "statutory-relevant figure; Book Depreciation also counts planned "
        "(draft) entries.",
    )
    book_residual = fields.Monetary(string="Book Residual Value", readonly=True)
    difference = fields.Monetary(
        string="Difference (Book − Tax)", readonly=True,
        help="Book depreciation minus tax depreciation for the year — the "
        "income-tax base adjustment (SK pripočítateľná/odpočítateľná položka, "
        "CZ § 23 ods. 3).",
    )

    # ------------------------------------------------------------------
    # Bridge contract
    # ------------------------------------------------------------------
    def _book_sql(self):
        """Edition-specific accounting (book) depreciation aggregation.

        Must return a SELECT producing one row per (asset, year) with the
        columns ``asset_id, fiscal_year, book_amount, book_amount_posted,
        book_residual`` — the same year semantics as the bridge's
        ``_cssk_book_depreciation_by_year()`` (all non-cancelled depreciation,
        posted subset in ``book_amount_posted``).
        """
        raise NotImplementedError

    def _report_query(self):
        return REPORT_QUERY_TEMPLATE % {"book_sql": self._book_sql()}

    def init(self):
        if self._abstract:
            return
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"CREATE OR REPLACE VIEW {self._table} AS ({self._report_query()})"
        )
