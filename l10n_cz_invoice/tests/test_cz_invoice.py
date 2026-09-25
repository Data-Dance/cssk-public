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
