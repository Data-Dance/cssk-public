# -*- coding: utf-8 -*-
from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_payment_method(self):
        # The receipt needs the flag to tell an order that still owes a
        # message ("tržba bude odeslána dodatečně") from one out of scope.
        # (pos.config loads every field, so its EET fields need no loader.)
        params = super()._loader_params_pos_payment_method()
        params["search_params"]["fields"].append("l10n_cz_eet2_contact_payment")
        return params
