# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVatRegistrationCategory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Odberateľ s.r.o."})

    def test_parsing_accepts_what_the_register_actually_writes(self):
        parse = self.env["res.partner"]._l10n_sk_parse_vat_registration_category
        self.assertEqual(parse("§4"), "4")
        self.assertEqual(parse("§ 7a"), "7a")
        self.assertEqual(parse("7A"), "7a")
        self.assertEqual(parse("§4b"), "4b")
        # These arrive via HTML/PDF scrapes and carry every kind of space.
        self.assertEqual(parse("§\u00a07a"), "7a")
        self.assertEqual(parse("§\t7a\n"), "7a")

    def test_an_unknown_category_reads_as_unknown_not_as_non_payer(self):
        """The difference changes how an invoice is taxed, so never guess."""
        parse = self.env["res.partner"]._l10n_sk_parse_vat_registration_category
        for value in ("§ 12", "platiteľ", "", None, "§4x"):
            self.assertFalse(parse(value), value)

    def test_only_par_4_family_makes_a_platitel(self):
        for category in ("4", "4b", "5", "6"):
            self.partner.l10n_sk_vat_registration_category = category
            self.assertTrue(self.partner.l10n_sk_is_full_vat_payer, category)
        for category in ("7", "7a"):
            self.partner.l10n_sk_vat_registration_category = category
            self.assertFalse(self.partner.l10n_sk_is_full_vat_payer, category)
        self.partner.l10n_sk_vat_registration_category = False
        self.assertFalse(self.partner.l10n_sk_is_full_vat_payer)


@tagged("post_install", "-at_install")
class TestReverseChargeWarning(AccountTestInvoicingCommon):
    """The warning only has a signal when l10n_sk_invoice supplies the flag."""

    # A real SK company with a chart of accounts and a sales journal — the
    # check is gated on the company's fiscal country being SK, so a bare
    # res.company would test nothing even if it could carry an invoice.
    chart_template = "sk"
    country_code = "SK"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.has_flag = "l10n_sk_reverse_charge" in cls.env["account.tax"]._fields
        cls.sk = cls.env.ref("base.sk")

    def _invoice(self, category, reverse_charge):
        partner = self.env["res.partner"].create(
            {
                "name": "Odberateľ",
                "country_id": self.sk.id,
                "l10n_sk_vat_registration_category": category,
            }
        )
        tax_vals = {
            "name": f"RC {category} {reverse_charge}",
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": self.env.company.id,
        }
        if self.has_flag:
            tax_vals["l10n_sk_reverse_charge"] = reverse_charge
        tax = self.env["account.tax"].create(tax_vals)
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_line_ids": [
                    (0, 0, {"name": "Práce", "quantity": 1, "price_unit": 100,
                            "tax_ids": [(6, 0, tax.ids)]}),
                ],
            }
        )

    def test_the_company_under_test_is_slovak(self):
        self.assertEqual(self.env.company.account_fiscal_country_id.code, "SK")

    def test_reverse_charge_to_a_par_7a_customer_is_flagged(self):
        if not self.has_flag:
            self.skipTest("l10n_sk_invoice not installed — no reverse-charge flag")
        move = self._invoice("7a", True)
        self.assertIn("§ 69", move.l10n_sk_vat_registration_warning)
        self.assertIn("7a", move.l10n_sk_vat_registration_warning)

    def test_reverse_charge_to_a_platitel_is_fine(self):
        self.assertFalse(self._invoice("4", True).l10n_sk_vat_registration_warning)

    def test_a_par_7a_customer_without_reverse_charge_is_fine(self):
        self.assertFalse(self._invoice("7a", False).l10n_sk_vat_registration_warning)

    def test_an_unknown_category_raises_nothing(self):
        self.assertFalse(self._invoice(False, True).l10n_sk_vat_registration_warning)

    def test_the_warning_never_blocks_the_posting(self):
        move = self._invoice("7a", True)
        move.action_post()
        self.assertEqual(move.state, "posted")
        if self.has_flag:
            self.assertTrue(
                move.message_ids.filtered(lambda m: "§ 69" in (m.body or ""))
            )
