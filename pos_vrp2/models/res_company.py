import json

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # ------------------------------------------------------------------
    # Tax mapping: VRP2 vatId <-> Odoo tax
    #
    # Only POS needs this: the catalog sync pushes/pulls per-product VAT and
    # POS sale receipts itemize VAT. Invoice-payment receipts carry no VAT
    # breakdown, so l10n_sk_vrp2_account does not use any of this.
    # ------------------------------------------------------------------

    vrp2_tax_0 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 0%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )
    vrp2_tax_5 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 5%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )
    vrp2_tax_10 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 10%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )
    vrp2_tax_19 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 19%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )
    vrp2_tax_20 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 20%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )
    vrp2_tax_23 = fields.Many2one(
        "account.tax",
        string="VRP2 Tax 23%",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', id)]",
    )

    vrp2_vatlist_json = fields.Text(
        string="VRP2 VAT List (cached)", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # VAT mapping helpers
    # ------------------------------------------------------------------

    def _vrp2_vatlist(self):
        self.ensure_one()
        if not self.vrp2_vatlist_json:
            return []
        try:
            return json.loads(self.vrp2_vatlist_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def _vrp2_vat_rate_to_tax_field(self):
        """Return {vat_rate_pct_int: account.tax record}."""
        self.ensure_one()
        result = {}
        for pct in (0, 5, 10, 19, 20, 23):
            tax = getattr(self, f"vrp2_tax_{pct}", None)
            if tax:
                result[pct] = tax
        return result

    def _vrp2_vat_id_to_tax(self):
        """Return {vrp2_vat_id: odoo_tax_id} for pulling from VRP2."""
        self.ensure_one()
        rate_to_tax = self._vrp2_vat_rate_to_tax_field()
        result = {}
        for entry in self._vrp2_vatlist():
            vat_id = entry.get("id")
            rate_pct = int(round(entry.get("vatRate", 0) * 100))
            tax = rate_to_tax.get(rate_pct)
            if vat_id and tax:
                result[vat_id] = tax.id
        return result

    def _vrp2_tax_to_vat_id(self):
        """Return {odoo_tax_id: vrp2_vat_id} for pushing to VRP2."""
        self.ensure_one()
        rate_to_tax = self._vrp2_vat_rate_to_tax_field()
        tax_id_to_rate = {tax.id: pct for pct, tax in rate_to_tax.items()}

        rate_to_vat_id = {}
        for entry in self._vrp2_vatlist():
            rate_pct = int(round(entry.get("vatRate", 0) * 100))
            if rate_pct not in rate_to_vat_id:
                rate_to_vat_id[rate_pct] = entry["id"]

        result = {}
        for tax_id, rate_pct in tax_id_to_rate.items():
            vat_id = rate_to_vat_id.get(rate_pct)
            if vat_id is not None:
                result[tax_id] = vat_id
        return result
