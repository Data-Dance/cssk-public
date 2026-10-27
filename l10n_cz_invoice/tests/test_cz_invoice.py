# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzInvoice(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.country_id = cls.env.ref("base.cz")
        cls.eu_partner = cls.env["res.partner"].with_context(
            no_vat_validation=True).create({
                "name": "Berlin GmbH", "country_id": cls.env.ref("base.de").id,
                "vat": "DE123456788"})
        cls.sk_partner = cls.env["res.partner"].with_context(
            no_vat_validation=True).create({
                "name": "Domaci", "country_id": cls.env.ref("base.cz").id,
                "vat": "CZ46342958"})
        group = cls.tax_sale_a.tax_group_id.id
        cls.zero_tax = cls.env["account.tax"].create({
            "name": "EU 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "tax_group_id": group})
        cls.rc_tax = cls.env["account.tax"].create({
            "name": "RC 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "tax_group_id": group,
            "l10n_cz_invoice_reverse_charge": True})

    def _inv(self, partner, tax, post=True):
        return self.init_invoice("out_invoice", partner=partner,
                                 amounts=[100.0], taxes=tax, post=post)

    def test_intra_eu_phrase(self):
        inv = self._inv(self.eu_partner, self.zero_tax)
        self.assertIn("§64", inv.l10n_cz_legal_notes)

    def test_reverse_charge_phrase(self):
        # Draft is enough — the phrase computes from the tax flag; posting a
        # reverse-charge line additionally requires the EE supply-code which is
        # out of scope here.
        inv = self._inv(self.sk_partner, self.rc_tax)
        self.assertIn("§92a", inv.l10n_cz_legal_notes)

    def test_render_has_dic_and_phrase(self):
        inv = self._inv(self.eu_partner, self.zero_tax)
        inv.l10n_cssk_constant_symbol = "0308"
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", inv.ids)[0].decode()
        # The DIČ label comes from core, which prints the fiscal country's
        # `vat_label` — "DIČ" for Czechia. This module adds no line of its own,
        # because in Czech usage DIČ *is* the VAT number core already shows.
        self.assertIn(self.eu_partner.vat, html)
        self.assertIn("§64", html)
        self.assertIn("0308", html)

    def test_the_customer_tax_id_is_printed_exactly_once(self):
        """Regression: a separate DIČ line duplicated the VAT number."""
        inv = self._inv(self.sk_partner, self.zero_tax)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", inv.ids)[0].decode()
        self.assertEqual(html.count(self.sk_partner.vat), 1)

    # -- goods vs services vs triangular trade --------------------------------
    def _zero(self, name, scope=None, **vals):
        return self.env["account.tax"].create({
            "name": "Test " + name, "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "tax_scope": scope,
            "tax_group_id": self.tax_sale_a.tax_group_id.id, **vals})

    def test_eu_service_says_the_customer_pays_the_tax(self):
        """A B2B service to another member state is not exempt under § 64: it
        is supplied there (§ 9 odst. 1) and § 29 odst. 2 písm. c) requires
        "daň odvede zákazník"."""
        inv = self._inv(self.eu_partner, self._zero("0% EU S", "service"))
        self.assertIn("Daň odvede zákazník", inv.l10n_cz_legal_notes)
        self.assertIn("§9 odst. 1", inv.l10n_cz_legal_notes)
        self.assertNotIn("§64", inv.l10n_cz_legal_notes)

    def test_eu_goods_and_services_print_both(self):
        inv = self.init_invoice(
            "out_invoice", partner=self.eu_partner, amounts=[100.0, 50.0],
            taxes=self.env["account.tax"], post=False)
        goods_tax = self._zero("0% EU G", "consu")
        service_tax = self._zero("0% EU S", "service")
        inv.invoice_line_ids[0].tax_ids = goods_tax
        inv.invoice_line_ids[1].tax_ids = service_tax
        self.assertIn("§64", inv.l10n_cz_legal_notes)
        self.assertIn("Daň odvede zákazník", inv.l10n_cz_legal_notes)

    def test_service_tax_without_scope_falls_back_to_the_product(self):
        product = self.env["product.product"].create(
            {"name": "Consulting", "type": "service"})
        inv = self.init_invoice(
            "out_invoice", partner=self.eu_partner, amounts=[100.0],
            taxes=self.zero_tax, post=False)
        inv.invoice_line_ids.product_id = product
        inv.invoice_line_ids.tax_ids = self.zero_tax
        self.assertIn("Daň odvede zákazník", inv.l10n_cz_legal_notes)
        self.assertNotIn("§64", inv.l10n_cz_legal_notes)

    def test_triangular_trade_states_it(self):
        """§ 29 odst. 2 písm. e): the middle person's invoice says it is a
        triangular trade; and the customer pays the tax (písm. c))."""
        tri = self._zero("0% EU T", "consu", l10n_cz_invoice_triangular=True)
        inv = self._inv(self.eu_partner, tri)
        self.assertIn("Třístranný obchod", inv.l10n_cz_legal_notes)
        self.assertIn("daň odvede zákazník", inv.l10n_cz_legal_notes)
        self.assertNotIn("§64", inv.l10n_cz_legal_notes)

    def test_export_of_services_cites_no_exemption(self):
        """§ 66 exempts the export of GOODS only."""
        us = self.env["res.partner"].create(
            {"name": "US Inc", "country_id": self.env.ref("base.us").id})
        inv = self._inv(us, self._zero("0% EX S", "service"))
        self.assertNotIn("§66", inv.l10n_cz_legal_notes or "")
        inv = self._inv(us, self._zero("0% EX G", "consu"))
        self.assertIn("§66", inv.l10n_cz_legal_notes)
