# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_sk_account_asset_profile.hooks import post_init_hook


def migrate(cr, version):
    """Installed before 19.0.1.1.0 on a company whose chart was already
    loaded, the module created no profiles; give them now. Idempotent."""
    post_init_hook(api.Environment(cr, SUPERUSER_ID, {}))
