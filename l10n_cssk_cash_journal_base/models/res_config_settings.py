# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """The regime is a settings choice, not something to hunt for on the company."""

    _inherit = "res.config.settings"

    cssk_bookkeeping_regime = fields.Selection(
        related="company_id.cssk_bookkeeping_regime", readonly=False,
    )
    cssk_cash_journal_start = fields.Date(
        related="company_id.cssk_cash_journal_start", readonly=False,
    )
