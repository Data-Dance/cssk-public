"""Map the prevailing NACE (new in 19.0.1.2.0) at res.partner.nace_code
when partner_nace is installed, unless a mapping was already chosen."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["partner.autocomplete.provider.ares_cz"]._ares_apply_default_mappings()
