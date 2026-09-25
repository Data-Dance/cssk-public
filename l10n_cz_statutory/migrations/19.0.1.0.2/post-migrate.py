from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_statutory.hooks import _seed_cz_tax_authorities


def migrate(cr, version):
    """Re-seed: adds the territorial workplaces (územní pracoviště) as children
    of the regional offices. Idempotent."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _seed_cz_tax_authorities(env)
