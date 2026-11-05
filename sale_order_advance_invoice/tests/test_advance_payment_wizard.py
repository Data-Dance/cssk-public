from odoo.tests import Form

from .common import AdvanceInvoiceCommon


class TestAdvancePaymentWizard(AdvanceInvoiceCommon):

    def test_payment_method_prefilled(self):
        """Opening the wizard fills the journal AND its payment method.

        Both used to be onchanges, and the one picking the journal ran after
        the one picking the payment method (its trigger field is not in the
        view), so the method stayed empty.
        """
        if not self.env["account.journal"].search_count([
            ("company_id", "=", self.env.company.id), ("type", "=", "bank"),
        ]):
            self.env["account.journal"].create({
                "name": "Bank", "code": "TBNK", "type": "bank",
            })
        advance = self._advance(self._order())
        wizard = Form(self.env["sale.order.manual.payment.wizard"].with_context(
            active_model="sale.order", active_id=advance.id))
        self.assertTrue(wizard.journal_id)
        self.assertTrue(wizard.payment_method_line_id)
        self.assertIn(
            wizard.payment_method_line_id,
            wizard.journal_id._get_available_payment_method_lines("inbound"))


class TestAdvanceProductName(AdvanceInvoiceCommon):

    def test_lazily_created_product_named_from_catalogue(self):
        """The advance product, created on first use, carries the catalogue's
        Slovak name rather than "Advance" (it appears on documents)."""
        self.env["res.lang"]._activate_lang("sk_SK")
        Imd = self.env["ir.model.data"]
        existing = self.env.ref(
            "sale_order_advance_invoice.product_advance_invoice", raise_if_not_found=False)
        if existing:
            # force the creation path: no xmlid, and nothing found by name
            existing.name = "Advance (old)"
            Imd.search([("module", "=", "sale_order_advance_invoice"),
                        ("name", "=", "product_advance_invoice")]).unlink()
        product = self.env["sale.order"]._get_advance_product().product_tmpl_id
        self.assertEqual(product.with_context(lang="en_US").name, "Advance")
        self.assertEqual(product.with_context(lang="sk_SK").name, "Preddavok")

    def test_helper_renames_only_given_languages(self):
        self.env["res.lang"]._activate_lang("sk_SK")
        product = self.env["sale.order"]._get_advance_product().product_tmpl_id
        product.with_context(lang="sk_SK").name = "Advance"
        product._advance_load_name_translations(["sk_SK"])
        self.assertEqual(product.with_context(lang="sk_SK").name, "Preddavok")
        self.assertEqual(product.with_context(lang="en_US").name, "Advance")
