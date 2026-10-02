# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import RecyclingFeeCommon


@tagged("post_install", "-at_install")
class TestRecyclingFeeSk(RecyclingFeeCommon):
    """Slovak rules: § 34 ods. 1 písm. d) and § 37 ods. 1 písm. a) zákona
    č. 79/2015 Z. z. — the statute's own word is "recyklačný poplatok"."""

    @classmethod
    @RecyclingFeeCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.sk = cls.env.ref("base.sk")
        cls.cz = cls.env.ref("base.cz")
        cls.sk_class = cls._classification(
            "SEWA small appliance", cls.sk, "fixed", [("2025-01-01", False, 0.9)],
        )
        cls.cz_class = cls._classification(
            "CZ small appliance", cls.cz, "fixed", [("2025-01-01", False, 6.0)],
        )
        cls.toaster = cls._product("Toaster", cls.sk_class | cls.cz_class)

    def test_sk_classification_in_eur(self):
        self.assertEqual(self.sk_class.currency_id, self.env.ref("base.EUR"))
        invoice = self._invoice([(self.toaster, 4, 25.0)])
        fee = invoice.invoice_line_ids.ecotax_line_ids
        self.assertEqual(fee.classification_id, self.sk_class)
        self.assertAlmostEqual(fee.amount_total, 3.6)

    def test_slovak_wording_on_the_invoice(self):
        invoice = self._invoice([(self.toaster, 4, 25.0)], post=True)
        text = invoice.invoice_line_ids._get_recycling_fee_texts()[0]
        self.assertTrue(text.startswith("z toho recyklačný poplatok"), text)
        html = self._render(invoice)
        self.assertIn("z toho recyklačný poplatok", html)
        self.assertIn("Recyklačný poplatok spolu bez DPH", html)
        self.assertNotIn("recyklační příspěvek", html)
