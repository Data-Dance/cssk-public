from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_vehicle_cap_amount = fields.Monetary(
        string="Tax Vehicle Depreciation Cap",
        help="Statutory limit for passenger vehicles flagged on the asset, in "
        "the company currency. CZ §30e: 2 000 000 CZK for category M1 — the "
        "tax board is computed on the limit. SK §17(34): 48 000 EUR — the "
        "board keeps the full depreciation and shows the conditional add-back "
        "separately. Leave at 0 for no limit.",
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
        help="Balance-sheet deferred-tax account (CZ/SK 481). The comparison "
        "trues this account's balance at the period end up to the deferred tax "
        "on asset depreciation, so use an account (e.g. an analytical 481 "
        "sub-account) that holds no other deferred tax.",
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
        (=max(diff,0), SK r. 150 / CZ ř. 50), "deduction" (=max(−diff,0),
        SK r. 250 / CZ ř. 150), "vehicle_addback" (SK § 17 ods. 34 — the
        add-back IF the statutory tax-base condition is met; the caller
        decides)}``. Tax = the annual tax-board lines in the
        period; book = the **posted** accounting depreciation of the same assets
        over the period (``_tax_accounting_depreciation_for_period``, the same
        source the reconciliation wizard uses) — NOT the draft-inclusive
        ``book_amount`` board column, which would overstate the filing whenever
        the year's depreciation moves are not yet all posted. Zeroes if the
        tax-asset bridge isn't installed.
        """
        self.ensure_one()
        empty = {"book": 0.0, "tax": 0.0, "difference": 0.0,
                 "addback": 0.0, "deduction": 0.0, "vehicle_addback": 0.0,
                 "b_book": 0.0, "b_tax": 0.0, "b_tax_gross": 0.0,
                 "b_suspended": 0.0, "b_sale": 0.0}
        Line = self.env["account.asset.tax.line"]
        if "asset_id" not in Line._fields:
            return empty
        years = list(range(date_from.year, date_to.year + 1))
        lines = Line.search([
            ("company_id", "=", self.id),
            ("fiscal_year", "in", years),
        ])
        tax = sum(lines.mapped("amount"))
        book_by_asset = {
            asset: asset._tax_accounting_depreciation_for_period(date_from, date_to)
            for asset in lines.mapped("asset_id")
        }
        book = sum(book_by_asset.values())
        diff = book - tax
        result = {
            "book": book, "tax": tax, "difference": diff,
            "addback": max(diff, 0.0), "deduction": max(-diff, 0.0),
            "vehicle_addback": sum(lines.mapped("vehicle_addback")),
        }
        result.update(self._cssk_asset_table_b(lines, book_by_asset))
        return result

    def _cssk_asset_table_b(self, lines, book_by_asset):
        """The SK DPPO Table B rows the register can state, tangible assets only.

        ``b_book``      r. 1 — posted accounting depreciation.
        ``b_tax``       what the tax board charges in the period (= r. 2 −
                        r. 4 + r. 5, the board's own figure).
        ``b_suspended`` r. 4 — § 22 ods. 9: the charge a suspended year would
                        have carried. The board writes a suspended year as 0
                        and pushes the schedule out by a year, so it is the
                        amount of the asset's next charged line.
        ``b_sale``      r. 5 — § 22 ods. 12: the whole-month part of the
                        annual charge in the year of disposal, on an asset
                        flagged ``tax_sk_disposal_months``. The poučenie keeps
                        it out of r. 2.
        ``b_tax_gross`` r. 2 — the board's figure before r. 4 and without
                        r. 5: ``b_tax − b_sale + b_suspended``.

        r. 3 (§ 19 ods. 3 písm. a), the unclaimed part of a leased asset's
        depreciation) is not held by the register and stays the accountant's.
        With it at 0, r. 6 = ``b_tax`` and r. 1 − r. 6 is the ``difference``
        above restricted to tangible assets.
        """
        tangible = lines.filtered(lambda line: line.asset_id._tax_is_tangible())
        b_tax = sum(tangible.mapped("amount"))
        b_book = sum(amount for asset, amount in book_by_asset.items()
                     if asset._tax_is_tangible())
        b_suspended = b_sale = 0.0
        for line in tangible:
            asset = line.asset_id
            if line.note == "suspended" and not line.amount:
                b_suspended += self._cssk_suspended_charge(line)
            elif asset.tax_sk_disposal_months:
                disposal = asset.tax_event_ids.filtered(
                    lambda event: event.event_type == "disposal")[:1]
                if disposal and disposal.date.year == line.fiscal_year:
                    b_sale += line.amount
        rnd = self.currency_id.round
        return {
            "b_book": rnd(b_book), "b_tax": rnd(b_tax),
            "b_tax_gross": rnd(b_tax - b_sale + b_suspended),
            "b_suspended": rnd(b_suspended), "b_sale": rnd(b_sale),
        }

    @staticmethod
    def _cssk_suspended_charge(line):
        """What a suspended board year would have charged had it run.

        ``apply_suspension`` keeps the queue of pending charges and pushes it
        out: the first suspended year of a run would have taken the next
        charged amount, the second the one after it, and so on.
        """
        board = line.asset_id.tax_line_ids.sorted("year_index")
        charged = board.filtered(lambda other: other.note != "suspended")
        before = charged.filtered(lambda other: other.year_index < line.year_index)
        last = before[-1:].year_index if before else 0
        run = len(board.filtered(
            lambda other: other.note == "suspended"
            and last < other.year_index < line.year_index))
        position = len(before) + run
        return charged[position].amount if position < len(charged) else 0.0

