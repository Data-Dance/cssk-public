# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestCzEcSalesSeed(TransactionCase):
    def test_version_seeded(self):
        version = self.env.ref("l10n_cz_ec_sales.dphshv_version_2025")
        self.assertEqual(version.country_id.code, "CZ")
        self.assertEqual(version.xml_root_element, "Pisemnost")
        self.assertEqual(len(version.statement_type_ids), 3)


@tagged("post_install", "-at_install")
class TestCzEcSales(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "CZ25663585", "city": "Praha"})
        # EPO requires the competent tax office (c_ufo); assign the seeded one.
        # FÚ pro hl. m. Prahu — seeded by l10n_cz_statutory's hook without an
        # xmlid (the old l10n_cssk_core.cz_ufo_* ids were removed in 1.2.0);
        # look it up by its stable submission code instead.
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701",
        })
        cls.tax_ic = cls.env["account.tax"].create({
            "name": "Intra-EU goods 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
            "tax_group_id": cls.tax_sale_a.tax_group_id.id,
            "cssk_ec_summary_code": "0",
        })
        cls.version = cls.env.ref("l10n_cz_ec_sales.dphshv_version_2025")

    def _statement(self):
        from odoo import fields
        today = fields.Date.context_today(self.env.user)
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": today.replace(day=1),
            "date_to": today.replace(day=28),
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_eu, amounts=[1000.0],
            taxes=self.tax_ic, post=True,
        )
        st = self._statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        self.assertEqual(st.line_ids.partner_country_code, "BE")
        self.assertEqual(st.line_ids.transaction_code, "0")
        self.assertAlmostEqual(st.line_ids.total_amount, 1000.0, places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Pisemnost")
        vetar = root.findall(".//VetaR")
        self.assertEqual(len(vetar), 1)
        self.assertEqual(vetar[0].get("k_stat"), "BE")
        self.assertEqual(vetar[0].get("c_vat"), "0477472701")
        self.assertEqual(vetar[0].get("pln_hodnota"), "1000")
