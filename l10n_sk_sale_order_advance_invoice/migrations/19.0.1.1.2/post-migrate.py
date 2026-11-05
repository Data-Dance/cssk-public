"""Name the advance journal and clearing account in Slovak, Czech and English.

Re-applies the spec: a journal or account still carrying a name we gave it gets
all three languages, one whose English name is already ours only gets the
missing ones, and anything the user renamed is left alone."""

from odoo import SUPERUSER_ID, api

from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.l10n_sk_sale_order_advance_invoice import SK_SPEC

    apply_advance_invoice_spec(env, "sk", SK_SPEC)
