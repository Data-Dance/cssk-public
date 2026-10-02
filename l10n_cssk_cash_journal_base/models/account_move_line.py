# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    """Per-line override of the account's denník category.

    One vendor bill routinely splits across several categories — a fuel receipt
    that is partly private, a bill carrying both zásoby and služby — and the
    account cannot say so. This is the same two-carrier arrangement the
    predkontácia design uses: the account supplies the default, the line
    overrides it.
    """

    _inherit = "account.move.line"

    cssk_cash_category_id = fields.Many2one(
        "cssk.cash.category",
        string="Cash Journal Category",
        help="Overrides the account's category when this line is paid.",
    )

    def _cssk_cash_category(self, direction=None):
        """The category this line contributes to the denník, or an empty set.

        Resolution order is the line's own override, then the account — and on
        the account, the direction decides: ``in`` prefers
        ``cssk_cash_category_in_id`` where the accountant has set one, because a
        loan account or ``343`` means a different column each way. A line with
        nothing resolves to nothing, and the caller turns that into a row
        flagged for review rather than into a guess.
        """
        self.ensure_one()
        if self.cssk_cash_category_id:
            return self.cssk_cash_category_id
        if direction == "in" and self.account_id.cssk_cash_category_in_id:
            return self.account_id.cssk_cash_category_in_id
        return self.account_id.cssk_cash_category_id
