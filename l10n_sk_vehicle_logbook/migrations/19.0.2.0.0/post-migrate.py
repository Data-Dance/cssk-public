# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_sk_vehicle_logbook.hooks import set_sk_advance_account


def migrate(cr, version):
    set_sk_advance_account(api.Environment(cr, SUPERUSER_ID, {}))
