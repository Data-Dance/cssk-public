# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Book the deducted half of the 19 % vehicle VAT on 343110.

    The tax shipped with 343120, the 23 % input-VAT account; Odoo's own 19 %
    purchase tax uses 343110. Only lines still on the shipped 343120 move, so
    an account somebody chose by hand is kept. Posted entries are not
    rewritten.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["account.chart.template"]._l10n_sk_vehicle_fix_19_account(
        env["res.company"].search([("chart_template", "=", "sk")])
    )
