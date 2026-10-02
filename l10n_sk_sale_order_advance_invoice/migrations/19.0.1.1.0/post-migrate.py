"""Wire the companies on the SK chart that were never wired: those whose chart
was loaded after, or in the same run as, this module's installation. Only
empty settings are filled."""

from odoo import SUPERUSER_ID, api

from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.l10n_sk_sale_order_advance_invoice import SK_SPEC

    apply_advance_invoice_spec(env, "sk", SK_SPEC)
