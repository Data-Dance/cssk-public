# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    """The regime is a settings choice, not something to hunt for on the company."""

    _inherit = "res.config.settings"

    cssk_bookkeeping_regime = fields.Selection(
        related="company_id.cssk_bookkeeping_regime", readonly=False,
    )
    cssk_cash_partial_allocation = fields.Selection(
        related="company_id.cssk_cash_partial_allocation", readonly=False,
    )
    cssk_cash_journal_start = fields.Date(
        related="company_id.cssk_cash_journal_start", readonly=False,
    )

    def action_cssk_map_chart_categories(self):
        """Apply the country's default account → category mapping.

        Offered as a button rather than run silently on every chart change: it
        writes on the chart, and an accountant should be the one who asks for
        that. It never overwrites a category somebody already chose.
        """
        self.ensure_one()
        touched = self.company_id._cssk_map_chart_categories()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if touched else "warning",
                "message": _(
                    "%s accounts mapped to cash journal categories.", touched,
                ) if touched else _(
                    "Nothing to map: either the chart is already mapped, or "
                    "there is no default mapping for this country.",
                ),
                "sticky": False,
            },
        }
