# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tag the intra-EU supply taxes of companies charted after the install.

Up to the previous version the codes were set only by the install hook, so a
company that got the l10n_cz chart later has untagged taxes and an empty
Souhrnné hlášení. The chart template now carries the codes for future
companies; this runs the hook once more for the existing ones. It skips a tax
that already has a code, so a code set by hand is kept.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cz_ec_sales.hooks import post_init_hook


def migrate(cr, version):
    if not version:
        return
    post_init_hook(api.Environment(cr, SUPERUSER_ID, {}))
