"""Recompute the tax-document deadline of every paid advance.

It used to be the earlier of 15 days and the month end for every company;
it is now the statutory deadline of the company's country (CZ 15 days, SK
the later of 15 days and the month end), and the stored value would
otherwise keep the old date until the advance is next paid.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env["sale.order"].with_context(active_test=False).search([
        ("is_advance_invoice", "=", True),
        ("advance_invoice_paid_date", "!=", False),
    ])
    if orders:
        env.add_to_compute(
            orders._fields["advance_invoice_accounting_date_due"], orders
        )
        orders.flush_recordset(["advance_invoice_accounting_date_due"])
