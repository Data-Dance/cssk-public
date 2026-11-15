# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVatRegistrationCategory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Odběratel s.r.o."})

    def test_parsing_accepts_what_the_register_actually_writes(self):
        parse = self.env["res.partner"]._l10n_cz_parse_vat_registration_category
        self.assertEqual(parse("PLATCE_DPH"), "payer")
        self.assertEqual(parse("SKUPINA_DPH"), "group")
        self.assertEqual(parse("IDENTIFIKOVANA_OSOBA"), "identified")
        self.assertEqual(parse("Identifikovaná osoba"), "identified")
        self.assertEqual(parse("plátce DPH"), "payer")
        self.assertEqual(parse("Neplátce"), "non_payer")
        # The selection's own keys, as another module would pass them.
        self.assertEqual(parse("non_payer"), "non_payer")
        self.assertEqual(parse("identified"), "identified")
        # Text copied from a page carries every kind of space.
        self.assertEqual(parse("identifikovaná osoba"), "identified")
        self.assertEqual(parse("\tPLATCE_DPH\n"), "payer")

    def test_an_unknown_category_reads_as_unknown_not_as_non_payer(self):
        """The difference changes how an invoice is taxed, so never guess.

        NENALEZEN is as often a mistyped DIČ as a neplátce, and a nespolehlivá
        osoba may or may not be an identifikovaná osoba."""
        parse = self.env["res.partner"]._l10n_cz_parse_vat_registration_category
        for value in ("NENALEZEN", "NESPOLEHLIVA_OSOBA", "§ 6", "", None, "ANO"):
            self.assertFalse(parse(value), value)

    def test_every_word_the_parser_knows_is_in_the_selection(self):
        from ..models.res_partner import CATEGORY_WORDS

        valid = dict(self.env["res.partner"]._fields[
            "l10n_cz_vat_registration_category"].selection)
        for category in CATEGORY_WORDS.values():
            self.assertIn(category, valid)

    def test_only_a_platce_and_a_skupina_are_platci(self):
        for category in ("payer", "group"):
            self.partner.l10n_cz_vat_registration_category = category
            self.assertTrue(self.partner.l10n_cz_is_full_vat_payer, category)
        for category in ("identified", "non_payer"):
            self.partner.l10n_cz_vat_registration_category = category
            self.assertFalse(self.partner.l10n_cz_is_full_vat_payer, category)
        self.partner.l10n_cz_vat_registration_category = False
        self.assertFalse(self.partner.l10n_cz_is_full_vat_payer)

    def test_the_fields_sit_on_the_contact_form_with_their_labels(self):
        arch = self.env["res.partner"].get_view(view_type="form")["arch"]
        self.assertIn('name="l10n_cz_vat_registration_category"', arch)
        self.assertIn('name="l10n_cz_vat_payer_since"', arch)


@tagged("post_install", "-at_install")
class TestReverseChargeWarning(AccountTestInvoicingCommon):
    """A § 92a supply is known by its tax: the row 25 tag, or a module's flag."""

    # A real CZ company with a chart of accounts and a sales journal — the
    # check is gated on the company's fiscal country being CZ, so a bare
    # res.company would test nothing even if it could carry an invoice.
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.cz = cls.env.ref("base.cz")
        cls.flag = next(
            (
                name
                for name in ("l10n_cz_invoice_reverse_charge", "l10n_cz_reverse_charge")
                if name in cls.env["account.tax"]._fields
            ),
            None,
        )
        cls.row_25 = cls.env["account.account.tag"]._get_tax_tags("VAT 25", cls.cz.id)

    def _tax(self, name, tagged_row_25=False, **vals):
        tags = [Command.set(self.row_25.ids)] if tagged_row_25 else []
        return self.env["account.tax"].create(
            {
                "name": name,
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": self.env.company.id,
                "invoice_repartition_line_ids": [
                    Command.create({"repartition_type": "base", "tag_ids": tags}),
                    Command.create({"repartition_type": "tax"}),
                ],
                "refund_repartition_line_ids": [
                    Command.create({"repartition_type": "base", "tag_ids": tags}),
                    Command.create({"repartition_type": "tax"}),
                ],
                **vals,
            }
        )

    def _invoice(self, category, tax, country=True, move_type="out_invoice"):
        partner = self.env["res.partner"].create(
            {
                "name": "Odběratel",
                "country_id": self.cz.id if country is True else country,
                "l10n_cz_vat_registration_category": category,
            }
        )
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": "2026-01-15",
                "invoice_line_ids": [
                    Command.create({
                        "name": "Stavební práce", "quantity": 1, "price_unit": 100,
                        "tax_ids": [Command.set(tax.ids)],
                    }),
                ],
            }
        )

    def test_the_company_under_test_is_czech(self):
        self.assertEqual(self.env.company.account_fiscal_country_id.code, "CZ")

    def test_the_row_25_tag_exists_in_the_czech_return(self):
        """The signal this module leans on when no flag is installed."""
        self.assertTrue(self.row_25)

    def test_reverse_charge_to_an_identifikovana_osoba_is_flagged(self):
        move = self._invoice("identified", self._tax("PDP IO", tagged_row_25=True))
        self.assertIn("§ 92a", move.l10n_cz_vat_registration_warning)
        self.assertIn("identifikovanou osobou", move.l10n_cz_vat_registration_warning)

    def test_reverse_charge_to_a_neplatce_is_flagged(self):
        move = self._invoice("non_payer", self._tax("PDP N", tagged_row_25=True))
        self.assertIn("§ 92a", move.l10n_cz_vat_registration_warning)
        self.assertIn("není plátcem DPH", move.l10n_cz_vat_registration_warning)

    def test_the_localization_s_own_reverse_charge_tax_is_recognised(self):
        """``l10n_cz``'s 0% RC sale tax, with nothing of ours configured."""
        tax = self.env["account.chart.template"].ref(
            "l10n_cz_tax_reverse_charge_mode", raise_if_not_found=False)
        if not tax:
            self.skipTest("l10n_cz no longer ships l10n_cz_tax_reverse_charge_mode")
        move = self._invoice("identified", tax)
        self.assertIn("§ 92a", move.l10n_cz_vat_registration_warning)

    def test_a_module_s_reverse_charge_flag_is_recognised_without_the_tag(self):
        if not self.flag:
            self.skipTest("no module with a § 92a flag on taxes is installed")
        move = self._invoice("identified", self._tax("PDP flag", **{self.flag: True}))
        self.assertIn("§ 92a", move.l10n_cz_vat_registration_warning)

    def test_a_tax_with_no_signal_keeps_the_check_quiet(self):
        move = self._invoice("identified", self._tax("0 % bez označení"))
        self.assertFalse(move.l10n_cz_vat_registration_warning)

    def test_reverse_charge_to_a_platce_or_a_skupina_is_fine(self):
        tax = self._tax("PDP P", tagged_row_25=True)
        for category in ("payer", "group"):
            self.assertFalse(
                self._invoice(category, tax).l10n_cz_vat_registration_warning,
                category,
            )

    def test_an_unknown_category_raises_nothing(self):
        tax = self._tax("PDP ?", tagged_row_25=True)
        self.assertFalse(self._invoice(False, tax).l10n_cz_vat_registration_warning)

    def test_a_foreign_customer_raises_nothing_and_no_country_still_warns(self):
        tax = self._tax("PDP zahr.", tagged_row_25=True)
        foreign = self._invoice("identified", tax, country=self.env.ref("base.sk").id)
        self.assertFalse(foreign.l10n_cz_vat_registration_warning)
        unknown = self._invoice("identified", tax, country=False)
        self.assertTrue(unknown.l10n_cz_vat_registration_warning)

    def test_vendor_bills_are_not_checked(self):
        tax = self._tax("PDP nákup", tagged_row_25=True, type_tax_use="purchase")
        bill = self._invoice("identified", tax, move_type="in_invoice")
        self.assertFalse(bill.l10n_cz_vat_registration_warning)

    def test_the_warning_never_blocks_the_posting(self):
        move = self._invoice("identified", self._tax("PDP post", tagged_row_25=True))
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertTrue(
            move.message_ids.filtered(lambda m: "§ 92a" in (m.body or ""))
        )
