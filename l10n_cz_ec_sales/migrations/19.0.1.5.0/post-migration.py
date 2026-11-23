# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Add the triangular-trade taxes to companies charted before this version.

The chart template carries them for companies charted from now on; this runs
the install hook once more for the existing ones. It adds only a tax a company
lacks and keeps an EC code set by hand.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_ec_sales.hooks import post_init_hook


def migrate(cr, version):
    if not version:
        return
    post_init_hook(api.Environment(cr, SUPERUSER_ID, {}))
