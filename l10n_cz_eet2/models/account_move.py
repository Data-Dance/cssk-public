# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # 17.0: ``account.payment`` delegates to its journal entry, so the entry is
    # where a payment becomes posted and where it stops being so. 18.0+ gave
    # the payment its own state and the hooks live on the payment there.

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        payments = posted.payment_id
        if payments:
            payments.sudo()._l10n_cz_eet2_try_register()
        return posted

    def button_draft(self):
        payments = self.payment_id
        if payments:
            payments.sudo()._l10n_cz_eet2_storno_registered()
        return super().button_draft()

    # No ``button_cancel`` override: core's cancels a posted entry by calling
    # ``button_draft`` first, so the storno is queued there, once.
