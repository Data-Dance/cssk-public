# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPaymentLine(models.Model):
    _inherit = "account.payment.line"

    def _get_payment_line_grouping_fields(self):
        """Lines with different symbols become different transfers.

        One transfer carries one set of symbols, so two bills of the same
        supplier due the same day, with different variable symbols, must not
        be merged into one payment: the supplier could match neither. Only
        for a SEPA credit transfer order that exports the symbols; other
        orders group as OCA does.
        """
        fields_list = super()._get_payment_line_grouping_fields()
        if self[:1].order_id._l10n_cssk_sepa_placement() == "none":
            return fields_list
        return fields_list + ["variable_symbol", "constant_symbol", "specific_symbol"]
