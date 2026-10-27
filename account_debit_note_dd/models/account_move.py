from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # NOTE: This module is a thin UI/report layer (see README) and deliberately
    # does NOT override posting. Up to 19.0.1.0.0 it carried a verbatim copy of
    # ``account.move._post`` that never called ``super()``: it dropped five core
    # validations (untrusted company bank account, negative total,
    # account/journal constraint, cross-company accounts, archived analytic
    # account) and the ``skip_recurring_copy`` context for every entry in the
    # database, and it silently cut off every ``_post`` extension loaded before
    # it. Removed in 19.0.1.0.1, as it was on the 18.0 port.
