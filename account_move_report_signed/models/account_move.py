from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _reverse_tax_totals(self, value):
        # This method is used to reverse the tax totals when the document is a refund. It will negate any value that has "amount" in its key, and will recursively apply this logic to any nested dictionaries or lists.
        if type(value) is dict:
            return {key: -val if (type(key) is str and "amount" in key) else self._reverse_tax_totals(val) for key, val in value.items()}
        elif type(value) is list:
            return [self._reverse_tax_totals(item) for item in value]
        else:
            return value
