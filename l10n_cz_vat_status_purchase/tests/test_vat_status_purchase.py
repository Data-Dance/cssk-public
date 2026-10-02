# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCzVatStatusPurchase(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        ref = cls.env["account.chart.template"].with_company(cls.company).ref
        cls.purch21 = ref("l10n_cz_21_receipt_domestic_supplies")
        cls.product = cls.env["product.product"].create({
            "name": "Materiál", "type": "consu", "standard_price": 100.0,
            "supplier_taxes_id": [Command.set(cls.purch21.ids)]})
        cls.partner = cls.env["res.partner"].create({"name": "Dodavatel"})

    def _order(self, day):
        form = Form(self.env["purchase.order"])
        form.partner_id = self.partner
        form.date_order = "%s 10:00:00" % day
        with form.order_line.new() as line:
            line.product_id = self.product
        return form.save()

    def test_order_taxes_follow_the_status_on_the_order_date(self):
        self.env["l10n.cz.vat.status.period"].create({
            "company_id": self.company.id, "date_from": "2026-07-01",
            "status": "non_payer"})
        self.assertEqual(self._order("2026-06-30").order_line.tax_ids, self.purch21)
        tax = self._order("2026-07-01").order_line.tax_ids
        self.assertEqual(tax.l10n_cz_vat_status_source_id, self.purch21)
        self.assertEqual(tax.l10n_cz_vat_status_kind, "nondeductible")

    def test_no_history_leaves_orders_alone(self):
        self.assertEqual(self._order("2026-07-01").order_line.tax_ids, self.purch21)
