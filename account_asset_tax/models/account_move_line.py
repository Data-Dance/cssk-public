from odoo import models
from odoo.tools import SQL


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _tax_capitalised_tax_by_line(self, taxes=None, in_currency=False):
        """``{base line id: amount}`` of the tax that these bill lines carry
        onto their own account, in company currency, signed like the line.

        That is the tax no VAT closing settles (a non-deductible leg,
        ``use_in_tax_closing`` false) booked on the account of the line it was
        computed from: a leg with no account of its own lands there. It is
        part of what the line costs, so on an asset line it is part of the
        asset's acquisition value. A non-deductible leg booked on an account of
        its own (an expense, say) is not.

        ``taxes`` narrows it to the legs of those taxes; ``in_currency``
        gives the amounts in the document's currency instead."""
        lines = self.filtered(lambda line: line.id and not line.tax_line_id)
        if not lines or (taxes is not None and not taxes):
            return {}
        query = self._get_query_tax_details_from_domain(
            [("move_id", "in", lines.move_id.ids)])
        tax_filter = (SQL("AND trl.tax_id IN %s", tuple(taxes.ids))
                      if taxes is not None else SQL())
        amount = SQL("tdq.tax_amount_currency" if in_currency
                     else "tdq.tax_amount")
        self.flush_model()
        self.env.cr.execute(SQL(
            """
            SELECT tdq.base_line_id, SUM(%(amount)s)
              FROM (%(query)s) AS tdq
              JOIN account_move_line tax_line ON tax_line.id = tdq.tax_line_id
              JOIN account_move_line base_line ON base_line.id = tdq.base_line_id
              JOIN account_tax_repartition_line trl
                ON trl.id = tdq.tax_repartition_line_id
             WHERE tdq.base_line_id IN %(ids)s
               AND trl.use_in_tax_closing IS NOT TRUE
               AND tax_line.account_id = base_line.account_id
               %(tax_filter)s
          GROUP BY tdq.base_line_id
            """,
            query=query, ids=tuple(lines.ids), tax_filter=tax_filter,
            amount=amount,
        ))
        return dict(self.env.cr.fetchall())
