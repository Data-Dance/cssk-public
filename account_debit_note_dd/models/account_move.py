from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # NOTE: This module is a thin UI/report layer (see README) and deliberately
    # does NOT override posting behaviour. Earlier 19.0 sources carried a
    # verbatim copy of ``account.move._post`` that only differed from core by
    # silently dropping five standard validations (untrusted company bank
    # account, negative-total check, account/journal constraint, cross-company
    # accounts, archived analytic account). That copy also pulled in 19.0-only
    # APIs (``deductible_amount``, ``non_deductible_*`` display types) absent in
    # 18.0. It was removed on the 18.0 port to restore full core posting
    # validation and match the documented module scope.
