# -*- coding: utf-8 -*-
from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _l10n_cz_eet2_is_registrable(self):
        """Closing a POS session books its takings as payments in the cash
        and bank journals. Those sales were registered order by order at the
        till; registering the session total again through a journal flagged
        as contact would evidence every sale twice."""
        self.ensure_one()
        if self.pos_session_id:
            return False
        return super()._l10n_cz_eet2_is_registrable()
