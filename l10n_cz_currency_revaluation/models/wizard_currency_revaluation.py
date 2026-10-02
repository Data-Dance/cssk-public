# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class WizardCurrencyRevaluation(models.TransientModel):
    _inherit = "wizard.currency.revaluation"

    def revaluate_currency(self):
        """Revalue at ČNB's actual rate of the revaluation date.

        A company on a fixed monthly rate (currency_rate_update_cz) books its
        documents at one rate per month, and that is what the ordinary rate
        table holds; the balance sheet must still be revalued at the rate of
        its own day (§ 24 odst. 6 ZoÚ). The context key makes currency
        conversion read the actual fixings kept for exactly this — and is
        inert where none are kept, so a company on daily rates is unaffected.
        """
        return super(
            WizardCurrencyRevaluation, self.with_context(cssk_actual_rates=True)
        ).revaluate_currency()
