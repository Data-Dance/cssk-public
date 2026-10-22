from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_statutory_footprint(self):
        res = super()._cssk_statutory_footprint()
        code = self._cssk_ec_transaction_code()
        if code is not False:
            res.append({
                "form": _("EC Sales List"),
                "code": _("code %s") % code,
                "name": _("EC Sales List (SV / SHV)")})
        return res

    def _cssk_ec_transaction_code(self):
        """Transaction code for the EC sales list, from the EC-tagged tax.
        Country modules override for special cases (e.g. triangulation)."""
        self.ensure_one()
        tax = self.tax_ids.filtered("cssk_ec_summary_code")[:1]
        return tax.cssk_ec_summary_code or False

    def _cssk_ec_amount(self):
        """Supply value in company currency, positive for supplies and
        negative for corrections (credit notes)."""
        self.ensure_one()
        sign = (
            -1.0
            if self.move_id.move_type in ("out_invoice", "out_refund")
            else 1.0
        )
        return sign * self.balance

    def _cssk_ec_partner_vat(self):
        self.ensure_one()
        return self.partner_id.commercial_partner_id.vat or ""
