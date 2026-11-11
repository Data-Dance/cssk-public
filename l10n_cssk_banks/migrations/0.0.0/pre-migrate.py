# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runs on every version change, before the data files load."""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cssk_banks.hooks import adopt_existing_banks


def migrate(cr, version):
    if not version:
        return
    adopt_existing_banks(api.Environment(cr, SUPERUSER_ID, {}))
