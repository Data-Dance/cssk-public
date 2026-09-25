import re

from odoo import api, models


def _digits_int(value):
    """The digits of ``value`` as an int (leading-zero tolerant compare),
    or None when there are none."""
    digits = re.sub(r"\D", "", value or "")
    return int(digits) if digits else None


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _cssk_open_advances_for_statement_line(self, st_line):
        """Advance invoices this statement line could pay: same company,
        not cancelled, with an unpaid remainder, matching partner when the
        line already carries one."""
        orders = self.search([
            ("is_advance_invoice", "=", True),
            ("company_id", "=", st_line.company_id.id),
            ("state", "!=", "cancel"),
        ]).filtered(
            lambda order: order.currency_id.compare_amounts(
                order.amount_total - order.amount_paid, 0.0
            )
            > 0
        )
        if st_line.partner_id:
            partner = st_line.partner_id.commercial_partner_id
            orders = orders.filtered(
                lambda order: order.partner_invoice_id.commercial_partner_id
                == partner
            )
        return orders

    @api.model
    def _cssk_find_advance_for_statement_line(self, st_line):
        """Match ``st_line`` to exactly one open advance.

        Returns ``(order, tier)`` where tier is ``"exact"`` (full advance
        number found in the line), ``"vs"`` (the line's structured variable
        symbol equals the advance's digits) or ``"digits"`` (a loose digit
        run equals the advance's digits) — or ``None``. More than one hit
        in the decisive tier bails out: an advance number is only unique
        per issuer, never globally.
        """
        keys = st_line._cssk_advance_matching_keys()
        if not any(keys.values()):
            return None
        orders = self._cssk_open_advances_for_statement_line(st_line)
        if not orders:
            return None

        exact = orders.filtered(lambda o: (o.name or "").upper() in keys["exact"])
        if exact:
            return (exact, "exact") if len(exact) == 1 else None

        for tier in ("vs", "digits"):
            tier_ints = {
                value
                for value in map(_digits_int, keys[tier])
                if value is not None
            }
            if not tier_ints:
                continue
            hits = orders.filtered(
                lambda o: _digits_int(o.name) in tier_ints
            )
            if hits:
                return (hits, tier) if len(hits) == 1 else None
        return None
