# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import RecyclingFeeCommon


@tagged("post_install", "-at_install")
class TestRecyclingFeeCz(RecyclingFeeCommon):
    """Czech rules: § 73 zákona č. 542/2020 Sb. and MŽP's guideline on it."""

    @classmethod
    @RecyclingFeeCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.cz = cls.env.ref("base.cz")
        cls.sk = cls.env.ref("base.sk")
        cls.kettle_class = cls._classification(
            "Small household appliance", cls.cz, "fixed",
            [("2025-01-01", "2025-12-31", 5.0), ("2026-01-01", False, 6.0)],
            categ_id=cls.env.ref("l10n_cssk_recycling_fee.categ_eee_5").id,
        )
        cls.speaker_class = cls._classification(
            "Consumer electronics per kg", cls.cz, "weight_based",
            [("2025-01-01", False, 0.5)],
        )
        cls.sk_class = cls._classification(
            "SK small appliance", cls.sk, "fixed", [("2025-01-01", False, 0.9)],
        )
        cls.battery_class = cls._classification(
            "Portable battery", cls.cz, "fixed", [("2025-01-01", False, 0.4)],
            disclose=False,
            categ_id=cls.env.ref("l10n_cssk_recycling_fee.categ_bat_portable").id,
        )
        cls.kettle = cls._product("Kettle", cls.kettle_class | cls.sk_class)
        cls.speaker = cls._product("Speaker", cls.speaker_class, weight=2.0)
        cls.battery = cls._product("AA cell", cls.battery_class)

    def _fee(self, invoice, product):
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == product)
        return line.ecotax_line_ids

    # --- pricing -----------------------------------------------------------

    def test_rate_follows_the_invoice_date(self):
        """A tariff change on 1 January must not reprice last year's invoice."""
        old = self._invoice([(self.kettle, 3, 405.0)], invoice_date="2025-06-30")
        new = self._invoice([(self.kettle, 3, 405.0)], invoice_date="2026-03-15")
        self.assertEqual(self._fee(old, self.kettle).amount_total, 15.0)
        self.assertEqual(self._fee(new, self.kettle).amount_total, 18.0)
        old.invoice_date = "2026-01-01"
        self.assertEqual(self._fee(old, self.kettle).amount_unit, 6.0)

    def test_only_the_selling_companys_market_applies(self):
        """The kettle carries a CZ and an SK classification; a Czech invoice
        must charge the Czech one only."""
        invoice = self._invoice([(self.kettle, 1, 405.0)])
        fee = self._fee(invoice, self.kettle)
        self.assertEqual(fee.classification_id, self.kettle_class)

    def test_weight_based_rate(self):
        """MŽP example 3: 0,50 Kč/kg × 2 kg = 1,00 Kč per piece, 100 pieces."""
        invoice = self._invoice([(self.speaker, 100, 501.0)])
        fee = self._fee(invoice, self.speaker)
        self.assertEqual(fee.amount_unit, 1.0)
        self.assertEqual(fee.amount_total, 100.0)
        self.assertEqual(fee.unit_weight, 2.0)
        text = fee._get_recycling_fee_text()
        self.assertTrue(text.startswith("z toho recyklační příspěvek"), text)
        self.assertIn("/kg ×", text)
        self.assertIn("/ks)", text)

    def test_fee_is_per_piece_not_per_line_unit(self):
        """Sold by the dozen, the fee is owed on twelve pieces each."""
        dozen = self.env.ref("uom.product_uom_dozen")
        invoice = self._invoice(
            [(self.kettle, 2, 4800.0, {"product_uom_id": dozen.id})]
        )
        fee = self._fee(invoice, self.kettle)
        self.assertEqual(fee.product_qty, 24.0)
        self.assertEqual(fee.amount_total, 144.0)

    def test_distributor_fixed_amount_wins_over_the_tariff(self):
        """A distributor shows what its supplier actually paid (MŽP 2.7)."""
        product = self._product("Import kettle", self.kettle_class, force=3.5)
        invoice = self._invoice([(product, 2, 405.0)])
        fee = self._fee(invoice, product)
        self.assertEqual(fee.amount_unit, 3.5)
        self.assertEqual(fee.amount_total, 7.0)

    def test_foreign_currency_prints_original_amount_and_rate(self):
        """MŽP 2.5: a EUR invoice converts, then shows the CZK amount and rate."""
        eur = self.setup_other_currency("EUR", rates=[("2025-01-01", 0.04)])
        invoice = self._invoice([(self.kettle, 10, 20.0)], currency=eur)
        fee = self._fee(invoice, self.kettle)
        self.assertEqual(fee.currency_id, eur)
        self.assertEqual(fee.rate_currency_id, self.company.currency_id)
        self.assertAlmostEqual(fee.amount_unit, 0.24)
        self.assertAlmostEqual(fee.amount_total, 2.4)
        self.assertAlmostEqual(fee.amount_total_rate_currency, 60.0)
        self.assertAlmostEqual(fee.exchange_rate, 25.0)
        text = fee._get_recycling_fee_text()
        self.assertIn("kurz", text)
        self.assertIn("CZK/EUR", text)

    def test_classification_without_country_stays_upstream(self):
        """The vendored OCA behaviour is untouched when no country is set."""
        generic = self.env["account.ecotax.classification"].create(
            {
                "name": "Generic ecotax",
                "ecotax_type": "fixed",
                "default_fixed_ecotax": 2.0,
                "product_status": "M",
                "supplier_status": "MAN",
            }
        )
        product = self._product("Lamp", generic)
        invoice = self._invoice([(product, 4, 50.0)])
        fee = self._fee(invoice, product)
        self.assertEqual(fee.amount_total, 8.0)
        self.assertFalse(fee.rate_currency_id)
        self.assertFalse(invoice.recycling_fee_statutory)
        self.assertEqual(fee._get_recycling_fee_text(), "")

    # --- presentation ------------------------------------------------------

    def test_printed_on_the_invoice_line_and_in_the_totals(self):
        invoice = self._invoice([(self.kettle, 100, 405.0)], post=True)
        html = self._render(invoice)
        self.assertIn("z toho recyklační příspěvek", html)
        self.assertIn("Recyklační příspěvek celkem bez DPH", html)
        # OCA's English column and total give way to the statutory wording.
        self.assertNotIn("Eco Part", html)

    def test_portable_battery_fee_is_never_printed(self):
        """§ 85 odst. 3: kept in the price and reported, never disclosed."""
        invoice = self._invoice(
            [(self.battery, 10, 30.0), (self.kettle, 1, 405.0)], post=True
        )
        battery_fee = self._fee(invoice, self.battery)
        self.assertEqual(battery_fee.amount_total, 4.0)
        self.assertEqual(
            invoice.invoice_line_ids.filtered(
                lambda l: l.product_id == self.battery
            )._get_recycling_fee_texts(),
            [],
        )
        self.assertEqual(invoice.recycling_fee_disclosed, 6.0)
        html = self._render(invoice)
        self.assertEqual(html.count("z toho recyklační příspěvek"), 1)
        report = self.env["recycling.fee.report"].search(
            [("move_id", "=", invoice.id), ("product_id", "=", self.battery.id)]
        )
        self.assertEqual(report.fee_amount, 4.0)

    def test_price_including_vat_says_the_fee_is_without_vat(self):
        tax = self.tax_sale_a.copy(
            {"name": "21% incl.", "price_include_override": "tax_included"}
        )
        invoice = self._invoice(
            [(self.kettle, 1, 490.0, {"tax_ids": [Command.set(tax.ids)]})]
        )
        line = invoice.invoice_line_ids
        self.assertIn("bez DPH", line._get_recycling_fee_texts()[0])

    def test_on_top_presentation_wording(self):
        self.company.recycling_fee_presentation = "on_top"
        invoice = self._invoice([(self.kettle, 1, 399.0)])
        text = invoice.invoice_line_ids._get_recycling_fee_texts()[0]
        self.assertTrue(
            text.startswith("recyklační příspěvek (samostatná položka)"), text
        )

    # --- safety nets -------------------------------------------------------

    def test_posting_without_a_valid_rate_is_refused(self):
        future = self._classification(
            "Not yet priced", self.cz, "fixed", [("2027-01-01", False, 1.0)]
        )
        product = self._product("Future gadget", future)
        invoice = self._invoice([(product, 1, 10.0)], invoice_date="2026-03-15")
        with self.assertRaisesRegex(UserError, "No recycling fee rate"):
            invoice.action_post()

    def test_posted_invoice_is_not_repriced_by_later_edits(self):
        """Correcting a tariff or a weight must not rewrite what was charged
        and declared; a reset to draft prices afresh."""
        invoice = self._invoice([(self.speaker, 10, 501.0)], post=True)
        fee = self._fee(invoice, self.speaker)
        self.assertEqual(fee.amount_total, 10.0)
        self.speaker_class.rate_ids.amount = 0.8
        self.speaker.weight = 3.0
        self.env.flush_all()
        fee.invalidate_recordset()
        self.assertEqual(fee.amount_total, 10.0)
        invoice.button_draft()
        self.assertEqual(fee.amount_total, 24.0)

    def test_posting_prices_on_the_date_set_by_posting(self):
        """An invoice posted without a date is priced on the date posting
        gives it, not left at whatever the draft was computed with."""
        invoice = self._invoice([(self.kettle, 1, 405.0)])
        invoice.invoice_date = False
        invoice.action_post()
        fee = self._fee(invoice, self.kettle)
        expected = self.kettle_class._get_rate(invoice.invoice_date).amount
        self.assertEqual(fee.amount_total, expected)

    def test_overlapping_rates_are_refused(self):
        with self.assertRaises(ValidationError):
            self._classification(
                "Overlap", self.cz, "fixed",
                [("2025-01-01", "2025-12-31", 1.0), ("2025-06-01", False, 2.0)],
            )

    def test_current_rate_mirrors_into_oca_fields(self):
        """OCA product screens read ``default_fixed_ecotax``; it follows the
        rate in force today, and the cron rolls it over."""
        today = fields.Date.context_today(self.env.user)
        classification = self._classification(
            "Mirror", self.cz, "fixed",
            [
                (today - timedelta(days=30), today - timedelta(days=1), 5.0),
                (today, False, 7.0),
            ],
        )
        self.assertEqual(classification.default_fixed_ecotax, 7.0)
        classification.default_fixed_ecotax = 0.0
        self.env["account.ecotax.classification"]._cron_refresh_current_rate()
        self.assertEqual(classification.default_fixed_ecotax, 7.0)

    # --- period report -----------------------------------------------------

    def test_period_report_nets_credit_notes(self):
        self._invoice([(self.speaker, 3, 501.0)], post=True)
        self._invoice(
            [(self.speaker, 1, 501.0)], move_type="out_refund", post=True
        )
        self._invoice([(self.speaker, 50, 501.0)])  # draft: not reported
        rows = self.env["recycling.fee.report"].search(
            [("product_id", "=", self.speaker.id)]
        )
        self.assertEqual(sum(rows.mapped("pieces")), 2.0)
        self.assertEqual(sum(rows.mapped("weight_kg")), 4.0)
        self.assertEqual(sum(rows.mapped("fee_amount")), 2.0)
        self.assertEqual(rows.currency_id, self.company.currency_id)

        content, report_type = self.env["ir.actions.report"]._render_xlsx(
            "l10n_cssk_recycling_fee.action_recycling_fee_xlsx", rows.ids, None
        )
        self.assertEqual(report_type, "xlsx")
        self.assertTrue(content.startswith(b"PK"))
