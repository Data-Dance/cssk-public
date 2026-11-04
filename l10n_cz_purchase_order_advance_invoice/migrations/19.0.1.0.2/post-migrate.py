"""Give the 314001 clearing account an English name.

Earlier versions created it with only its Czech name, stored as the English
source, so an English-speaking user saw Czech. Re-applying the spec renames
an account that still has that name; one the user renamed is left alone."""

from odoo import SUPERUSER_ID, api

from odoo.addons.purchase_order_advance_invoice.tools import apply_purchase_advance_spec


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.l10n_cz_purchase_order_advance_invoice import CZ_SPEC

    apply_purchase_advance_spec(env, "cz", CZ_SPEC)
