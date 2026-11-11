# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runs on every version change, after the data files load (and after any
versioned post script, which Odoo orders before 0.0.0)."""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cssk_banks.hooks import sync_registry


def migrate(cr, version):
    if not version:
        return
    sync_registry(api.Environment(cr, SUPERUSER_ID, {}))
