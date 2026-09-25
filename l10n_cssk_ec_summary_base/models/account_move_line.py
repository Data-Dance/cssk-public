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
                "name": _("EC Sales List (SV / SHV)"),
                "res_model": "cssk.ec.summary.statement"})
        return res

    def _cssk_ec_transaction_code(self):
        """Transaction code for the EC sales list, from the EC-tagged tax.
        Country modules override for special cases (e.g. triangulation)."""
        self.ensure_one()
        tax = self.tax_ids.filtered("cssk_ec_summary_code")[:1]
        return tax.cssk_ec_summary_code or False

    def _cssk_ec_amount(self):
        """Supply value in company currency, positive for supplies and
        negative for corrections (credit notes).

        ⚠️ The sign does NOT depend on the move type, and reading it from there
        was a bug. Every tax carrying ``cssk_ec_summary_code`` is a **sale-side**
        tax — that is what puts a supply on this report at all — so a line that
        reaches this method is on the supply side by construction, whatever
        shape the document happens to have. Taking the sign from the document
        instead assumed an invoice, and an imported supply posted as a journal
        ENTRY then arrived with its sign inverted.

        Found on the first measurement of the súhrnný výkaz ever made against
        filed data: a synthesised base line of −1 836.07 on an ``entry``,
        reported as −1 836.07 where the filing has +2 235.57. Sixteen of the
        eighteen comparable rows matched because those documents stayed
        invoices; the one that did not was the one that exposed the assumption.

        The credit-note case still works and needs no special handling: a
        correction's base sits on the opposite side, so the same sign yields a
        negative amount by arithmetic rather than by a second rule.
        """
        self.ensure_one()
        return -1.0 * self.balance

    def _cssk_ec_partner_vat(self):
        self.ensure_one()
        return self.partner_id.commercial_partner_id.vat or ""
