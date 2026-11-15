"""Point the register mappings (new in 19.0.1.4.0) at the fields of
l10n_cz_trade_registry where that module is installed, unless a mapping was
already chosen."""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["partner.autocomplete.provider.ares_cz"]._ares_apply_default_mappings()
