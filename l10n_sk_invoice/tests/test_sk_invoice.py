import re

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkInvoice(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.country_id = cls.env.ref("base.sk")
        cls.company.partner_id.l10n_sk_dic = "2020999999"

        cls.eu_partner = cls.env["res.partner"].with_context(
            no_vat_validation=True
        ).create({
            "name": "Berlin GmbH",
            "country_id": cls.env.ref("base.de").id,
            "vat": "DE123456788",
            "l10n_sk_dic": "DE-DIC-1",
        })
        cls.sk_partner = cls.env["res.partner"].with_context(
            no_vat_validation=True
        ).create({
            "name": "Bratislava s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "vat": "SK2023456787",
            "l10n_sk_dic": "2023456787",
        })
        group = cls.tax_sale_a.tax_group_id.id
        cls.zero_tax = cls.env["account.tax"].create({
            "name": "EU 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "tax_group_id": group,
        })
        cls.rc_tax = cls.env["account.tax"].create({
            "name": "RC 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "tax_group_id": group,
            "l10n_sk_reverse_charge": True,
        })

    def _invoice(self, partner, tax):
        return self.init_invoice(
            "out_invoice", partner=partner, amounts=[100.0], taxes=tax, post=True
        )

    def test_intra_eu_supply_phrase(self):
        inv = self._invoice(self.eu_partner, self.zero_tax)
        self.assertIn("§43", inv.l10n_sk_legal_notes)
        self.assertIn("Intra-Community", inv.l10n_sk_legal_notes)

    def test_reverse_charge_phrase(self):
        inv = self._invoice(self.sk_partner, self.rc_tax)
        self.assertIn("§69 ods. 12", inv.l10n_sk_legal_notes)

    def test_domestic_standard_has_no_exemption_phrase(self):
        inv = self._invoice(self.sk_partner, self.zero_tax)
        # Domestic 0% with no RC flag -> no §43/§47/§69 phrase auto-added.
        self.assertNotIn("§43", inv.l10n_sk_legal_notes or "")
        self.assertNotIn("§69", inv.l10n_sk_legal_notes or "")

    def test_variable_symbol_from_name(self):
        inv = self._invoice(self.sk_partner, self.zero_tax)
        self.assertEqual(
            inv.l10n_cssk_variable_symbol, re.sub(r"\D", "", inv.name)
        )

    def test_manual_note_appended(self):
        inv = self._invoice(self.sk_partner, self.zero_tax)
        inv.l10n_sk_legal_note_manual = "Tovar dodaný podľa zmluvy č. 5."
        self.assertIn("zmluvy č. 5", inv.l10n_sk_legal_notes)

    def test_report_renders_sk_content(self):
        inv = self._invoice(self.eu_partner, self.zero_tax)
        inv.l10n_cssk_constant_symbol = "0308"
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", inv.ids
        )[0].decode()
        self.assertIn("DIČ", html)
        self.assertIn("§43", html)
        self.assertIn("0308", html)
