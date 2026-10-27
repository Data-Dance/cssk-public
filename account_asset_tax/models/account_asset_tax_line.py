from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAssetTaxLine(models.Model):
    """One year (or §30a month) of the tax-depreciation schedule.

    These lines are **never posted to the general ledger** — tax depreciation is
    a tax-base item, not an accounting expense. They are the Odoo persistence of
    :class:`engine.depreciation.ScheduleLine` and feed the year-end
    accounting-vs-tax reconciliation (SK DPPO r. 150 / 250, CZ ř. 50 / 150).

    The link to the asset (``asset_id``) is added by the bridge module
    (``account_asset_tax_ee`` / ``account_asset_tax_oca``) so that this core
    module depends on neither the Enterprise nor the OCA asset implementation.
    """

    _name = "account.asset.tax.line"
    _description = "Tax Depreciation Line"
    _order = "company_id, year_index, date_from"

    company_id = fields.Many2one(
        "res.company", required=True, index=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")

    year_index = fields.Integer(string="Year #", required=True)
    fiscal_year = fields.Integer(string="Fiscal Year")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    amount = fields.Monetary(string="Tax Depreciation")
    amount_cumulative = fields.Monetary(string="Cumulative")
    residual = fields.Monetary(string="Tax Residual Value")
    note = fields.Char()
    vehicle_addback = fields.Monetary(
        string="Vehicle Add-back (SK §17(34))",
        help="Slovakia, §17(34): for a passenger car with an entry price of "
        "48 000 EUR or more, the part of this year's tax depreciation above "
        "straight-line depreciation of 48 000 EUR. It is added back to the tax "
        "base only when that base is lower than the number of such cars × the "
        "annual straight-line depreciation of 48 000 EUR, and never by a "
        "lessor for a car leased without a purchase option. The depreciation "
        "itself stays on the board in full.",
    )

    # Accounting (book) depreciation lined up against this tax year — so the one
    # annual board shows both streams + their difference. Computed live from the
    # asset's accounting board (``_cssk_book_depreciation_by_year`` on the bridge),
    # matched by ``fiscal_year``; book depreciation booked monthly is aggregated
    # to the year. ``difference`` (book − tax) is the DPPO adjustment for the year.
    # A §30a board has one line per MONTH: the year's book figures then sit on
    # the year's last line only, so a sum over the lines counts them once.
    book_amount = fields.Monetary(
        string="Book Depreciation", compute="_compute_book_vs_tax",
    )
    book_residual = fields.Monetary(
        string="Book Residual Value", compute="_compute_book_vs_tax",
    )
    difference = fields.Monetary(
        string="Difference (Book − Tax)", compute="_compute_book_vs_tax",
        help="Book depreciation minus tax depreciation for the year — the "
        "income-tax base adjustment (SK pripočítateľná/odpočítateľná položka, "
        "CZ § 23 ods. 3).",
    )

    @api.depends("fiscal_year", "amount", "date_from")
    def _compute_book_vs_tax(self):
        has_asset = "asset_id" in self._fields
        for line in self:
            row = {}
            asset = line.asset_id if has_asset else False
            if asset and line._is_last_line_of_year():
                row = asset._cssk_book_depreciation_by_year().get(
                    line.fiscal_year) or {}
            line.book_amount = row.get("amount", 0.0)
            line.book_residual = row.get("residual", 0.0)
            line.difference = line.book_amount - line.amount

    def _is_last_line_of_year(self):
        """True for the asset's last board line of this fiscal year — the
        only line of an annual board, the December (or disposal) line of a
        monthly §30a one."""
        self.ensure_one()
        siblings = self.asset_id.tax_line_ids.filtered(
            lambda l: l.fiscal_year == self.fiscal_year)
        if not siblings or self not in siblings:
            return True
        last = max(siblings, key=lambda l: (l.date_from, l.year_index, l.id))
        return last == self

    # True once the fiscal year this line belongs to is closed / filed, so the
    # value is frozen and excluded from recomputation. Set by the wizard.
    posted = fields.Boolean(
        string="Filed",
        help="The fiscal year of this line has been filed; the figure is frozen "
        "and a recomputation will not move it.",
    )

    # Fields whose values constitute the filed (frozen) figure. Changing any of
    # them on a posted line — including un-filing it — requires the explicit
    # ``cssk_unfreeze`` context flag; the backfill wizard's mass unfreeze is the
    # sanctioned correction path.
    _FROZEN_LINE_FIELDS = (
        "amount", "amount_cumulative", "residual", "fiscal_year", "posted",
    )

    def write(self, vals):
        touched = [f for f in self._FROZEN_LINE_FIELDS if f in vals]
        if touched and not self.env.context.get("cssk_unfreeze"):
            for line in self.filtered("posted"):
                for fname in touched:
                    field = line._fields[fname]
                    if (field.convert_to_cache(vals[fname], line)
                            != field.convert_to_cache(line[fname], line)):
                        raise UserError(_(
                            "Tax depreciation line %(year)s of %(asset)s is "
                            "filed (frozen); %(field)s may not change. Use the "
                            "Backfill (migration) wizard to unfreeze and "
                            "rebuild the history.",
                            year=line.fiscal_year,
                            asset=line.asset_id.display_name
                            if "asset_id" in line._fields else line.display_name,
                            field=field.string or fname))
        return super().write(vals)
