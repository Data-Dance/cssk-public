# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestReceiptCaptureBase(AccountTestInvoicingCommon):
    """The framework, exercised with the figures from a real fuel receipt."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.cssk_receipt_expense_account_id = cls.company_data[
            "default_account_expense"]
        cls.tax_23 = cls.env["account.tax"].create({
            "name": "DPH 23% (test)",
            "amount_type": "percent",
            "amount": 23.0,
            "type_tax_use": "purchase",
            "company_id": cls.company.id,
        })
        cls.tax_19 = cls.env["account.tax"].create({
            "name": "DPH 19% (test)",
            "amount_type": "percent",
            "amount": 19.0,
            "type_tax_use": "purchase",
            "price_include_override": "tax_excluded",
            "company_id": cls.company.id,
        })

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _fuel_receipt(self):
        """The Vzorová čerpacia stanica receipt: 31.17 l Benzín 95, 57.85 gross at 23 %."""
        return self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Vzorová čerpacia stanica, a. s.",
            "seller_vat": "SK7199000006",
            "seller_tax_id": "2077000002",
            "seller_reg_id": "99000022",
            "seller_vat_payer": True,
            "premises_note": "Diaľnica D99, Skúšobné Pole",
            "issue_date": "2026-03-20 09:36:36",
            "amount_total": 57.85,
            "receipt_uid": "O-ABCDEF0000000002ABCDEF0000000002",
            "line_ids": [fields.Command.create({
                "name": "Benzín 95", "quantity": 31.17, "uom_label": "l",
                "vat_rate": 23.0, "amount_total": 57.85,
            })],
            "tax_summary_ids": [fields.Command.create({
                "vat_rate": 23.0, "amount_untaxed": 47.03, "amount_tax": 10.82,
            })],
        })

    # ------------------------------------------------------------------
    # arithmetic
    # ------------------------------------------------------------------
    def test_totals_come_from_the_recap(self):
        receipt = self._fuel_receipt()
        self.assertEqual(receipt.amount_untaxed, 47.03)
        self.assertEqual(receipt.amount_tax, 10.82)
        self.assertFalse(receipt._check_reconciliation())

    def test_line_amounts_are_derived_not_stored_wrong(self):
        receipt = self._fuel_receipt()
        line = receipt.line_ids
        self.assertEqual(line.amount_untaxed, 47.03)
        self.assertEqual(line.amount_tax, 10.82)
        self.assertEqual(line.quantity, 31.17)

    def test_totals_fall_back_to_lines_without_a_recap(self):
        receipt = self._fuel_receipt()
        receipt.tax_summary_ids.unlink()
        receipt.invalidate_recordset()
        self.assertEqual(receipt.amount_untaxed, 47.03)
        self.assertEqual(receipt.amount_tax, 10.82)

    # ------------------------------------------------------------------
    # reconciliation gates
    # ------------------------------------------------------------------
    def test_gate_catches_lines_not_summing_to_the_total(self):
        receipt = self._fuel_receipt()
        receipt.line_ids.amount_total = 50.00
        problems = receipt._check_reconciliation()
        self.assertTrue(problems)
        self.assertTrue(any("lines sum" in p for p in problems))

    def test_gate_catches_a_rate_the_recap_does_not_mention(self):
        """The check that would have caught a stale rate label.

        A provider trusting the legacy 'basic / reduced' recap would read 20 %
        where the items say 23 %. The bucket then matches nothing.
        """
        receipt = self._fuel_receipt()
        receipt.tax_summary_ids.vat_rate = 20.0
        problems = receipt._check_reconciliation()
        self.assertTrue(problems)
        self.assertTrue(any("does not mention" in p for p in problems))

    def test_gate_catches_a_bucket_that_disagrees_with_its_items(self):
        receipt = self._fuel_receipt()
        receipt.tax_summary_ids.write({"amount_untaxed": 40.0, "amount_tax": 9.2})
        problems = receipt._check_reconciliation()
        self.assertTrue(problems)
        self.assertTrue(any("VAT recap says" in p for p in problems))

    def test_gate_catches_base_plus_vat_not_equalling_the_total(self):
        receipt = self._fuel_receipt()
        receipt.amount_total = 60.00
        problems = receipt._check_reconciliation()
        self.assertTrue(any("does not equal the receipt total" in p
                            for p in problems))

    def test_three_rates_reconcile(self):
        """The restaurant bill: 5 % food, 19 % water, 23 % alcohol.

        The case the two-slot legacy recap cannot express at all.
        """
        receipt = self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Vzorová reštaurácia, s. r. o.",
            "issue_date": "2026-03-14 19:59:02",
            "amount_total": 181.90,
            "line_ids": [
                fields.Command.create({"name": "HLAVNÉ JEDLO Č. 1", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 14.90}),
                fields.Command.create({"name": "PREDJEDLO Č. 2", "quantity": 2,
                                       "vat_rate": 5.0, "amount_total": 17.80}),
                fields.Command.create({"name": "BBQ SET", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 48.00}),
                fields.Command.create({"name": "ZELENINOVÁ PRÍLOHA", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 7.90}),
                fields.Command.create({"name": "POLIEVKA PRE 2 OSOBY", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 32.00}),
                fields.Command.create({"name": "PREDJEDLO Č. 6", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 8.90}),
                fields.Command.create({"name": "Obal na jedlo", "quantity": 1,
                                       "vat_rate": 5.0, "amount_total": 1.00}),
                fields.Command.create({"name": "Miešaný nápoj", "quantity": 2,
                                       "vat_rate": 23.0, "amount_total": 19.80}),
                fields.Command.create({"name": "Destilát 40 %", "quantity": 1,
                                       "vat_rate": 23.0, "amount_total": 7.90}),
                fields.Command.create({"name": "Fľaša vína", "quantity": 1,
                                       "vat_rate": 23.0, "amount_total": 13.90}),
                fields.Command.create({"name": "Rum", "quantity": 2,
                                       "vat_rate": 23.0, "amount_total": 9.80}),
                fields.Command.create({"name": "Voda z vodovodu", "quantity": 1,
                                       "vat_rate": 19.0, "amount_total": 0.00}),
            ],
            "tax_summary_ids": [
                fields.Command.create({"vat_rate": 5.0, "amount_untaxed": 124.29,
                                       "amount_tax": 6.21}),
                fields.Command.create({"vat_rate": 23.0, "amount_untaxed": 41.79,
                                       "amount_tax": 9.61}),
                fields.Command.create({"vat_rate": 19.0, "amount_untaxed": 0.0,
                                       "amount_tax": 0.0}),
            ],
        })
        self.assertEqual(len(receipt.tax_summary_ids), 3)
        self.assertEqual(receipt.amount_untaxed, 166.08)
        self.assertEqual(receipt.amount_tax, 15.82)
        self.assertFalse(receipt._check_reconciliation())

    def test_force_captured_records_what_was_overridden(self):
        receipt = self._fuel_receipt()
        receipt.amount_total = 60.00
        receipt._post_capture()
        self.assertEqual(receipt.state, "review")
        self.assertTrue(receipt.review_reason)
        receipt.action_force_captured()
        self.assertEqual(receipt.state, "captured")

    # ------------------------------------------------------------------
    # seller resolution
    # ------------------------------------------------------------------
    def test_partner_matched_on_vat_regardless_of_spacing(self):
        partner = self.env["res.partner"].create({
            "name": "Vzorová čerpacia stanica, a. s.", "is_company": True,
            "vat": "SK 7199 000 006",
        })
        receipt = self._fuel_receipt()
        self.assertEqual(receipt._find_partner(), partner)

    def test_partner_matched_on_ico_when_vat_differs(self):
        """A VAT-group member's IČ DPH is not derivable from its DIČ.

        Vzorová čerpacia stanica files under the group number SK7199000006 while its own DIČ is
        2077000002, so IČO is the key that still works.
        """
        partner = self.env["res.partner"].create({
            "name": "Vzorová čerpacia stanica, a. s.", "is_company": True,
            "company_registry": "99000022",
        })
        receipt = self._fuel_receipt()
        self.assertEqual(receipt._find_partner(), partner)

    def test_created_partner_never_takes_the_premises_address(self):
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        self.assertEqual(receipt.partner_id.vat, "SK7199000006")
        self.assertEqual(receipt.partner_id.company_registry, "99000022")
        self.assertFalse(receipt.partner_id.street)

    # ------------------------------------------------------------------
    # tax resolution
    # ------------------------------------------------------------------
    def test_tax_for_rate_finds_the_purchase_tax(self):
        receipt = self._fuel_receipt()
        self.assertEqual(receipt._tax_for_rate(23.0), self.tax_23)
        self.assertEqual(receipt._tax_for_rate(19.0), self.tax_19)
        self.assertFalse(receipt._tax_for_rate(7.5))

    # ------------------------------------------------------------------
    # vendor-bill sink
    # ------------------------------------------------------------------
    def test_bill_in_summary_mode_posts_the_sellers_own_base(self):
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        move = receipt.action_create_bill()
        self.assertEqual(move.move_type, "in_receipt")
        self.assertEqual(move.state, "draft")
        self.assertEqual(len(move.invoice_line_ids), 1)
        self.assertEqual(move.invoice_line_ids.price_unit, 47.03)
        self.assertEqual(move.invoice_line_ids.quantity, 1.0)
        self.assertAlmostEqual(move.amount_tax, 10.82, places=2)
        self.assertAlmostEqual(move.amount_total, 57.85, places=2)
        self.assertEqual(receipt.state, "done")
        self.assertEqual(receipt.move_id, move)

    def test_bill_in_line_mode_keeps_quantity_one(self):
        """Per-item detail without the unit-price drift."""
        self.company.cssk_receipt_bill_detail = "lines"
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        move = receipt.action_create_bill()
        line = move.invoice_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.quantity, 1.0)
        self.assertEqual(line.price_unit, 47.03)
        self.assertIn("31.17", line.name)
        self.assertAlmostEqual(move.amount_total, 57.85, places=2)

    def test_bill_refused_when_a_rate_has_no_tax(self):
        """The failure that would otherwise post a receipt with no VAT at all."""
        self.tax_23.unlink()
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        with self.assertRaisesRegex(UserError, "No purchase tax is mapped"):
            receipt.action_create_bill()
        self.assertFalse(receipt.move_id)
        self.assertNotEqual(receipt.state, "done")

    def test_bill_refused_for_an_unreconciled_receipt(self):
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        with self.assertRaisesRegex(UserError, "captured, reconciled"):
            receipt.action_create_bill()

    def test_bill_not_created_twice(self):
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        receipt.action_create_bill()
        receipt.state = "captured"
        with self.assertRaisesRegex(UserError, "already has the vendor bill"):
            receipt.action_create_bill()


    # ------------------------------------------------------------------
    # gates added after an adversarial review
    # ------------------------------------------------------------------
    def test_gate_catches_value_shifted_between_base_and_tax(self):
        """A bucket that foots against its items can still state the wrong VAT.

        47.03 + 10.82 is the right gross at 23 %, but so is 45.00 + 12.85 —
        which overstates the deductible VAT by two euros while every total
        still agrees.
        """
        receipt = self._fuel_receipt()
        receipt.tax_summary_ids.write({
            "amount_untaxed": 45.00, "amount_tax": 12.85})
        problems = receipt._check_reconciliation()
        self.assertTrue(problems)
        self.assertTrue(any("at 23%" in p for p in problems), problems)

    def test_a_return_item_is_never_posted_unattended(self):
        """An unsigned negative item reconciles perfectly and is still wrong."""
        receipt = self._fuel_receipt()
        receipt.line_ids.is_negative = True
        problems = receipt._check_reconciliation()
        self.assertTrue(any("returns or corrections" in p for p in problems))

    def test_bill_refused_for_a_price_included_tax(self):
        """A bill line carries the net, so an included tax understates it."""
        self.tax_23.price_include_override = "tax_included"
        receipt = self._fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        with self.assertRaisesRegex(UserError, "tax-included"):
            receipt.action_create_bill()
        self.assertFalse(receipt.move_id)

    def test_per_rate_verification_catches_swapped_rates(self):
        """Two rates wrong in opposite directions leave every aggregate intact.

        Mapping 19 % to the 23 % tax and vice versa keeps the document's total
        VAT identical while reporting the wrong tax on each line of the return.
        """
        receipt = self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Swapped", "issue_date": "2026-03-14 10:00:00",
            "amount_total": 242.00, "state": "captured",
            "tax_summary_ids": [
                fields.Command.create({"vat_rate": 23.0,
                                       "amount_untaxed": 100.0,
                                       "amount_tax": 23.0}),
                fields.Command.create({"vat_rate": 19.0,
                                       "amount_untaxed": 100.0,
                                       "amount_tax": 19.0}),
            ],
        })
        receipt.action_create_partner()
        swapped = {23.0: self.tax_19, 19.0: self.tax_23}
        with patch.object(
                type(receipt), "_tax_for_rate",
                lambda self, rate: next(
                    (t for r, t in swapped.items() if abs(r - rate) < 0.001),
                    self.env["account.tax"])):
            with self.assertRaisesRegex(UserError, "is mapped to"):
                receipt.action_create_bill()
        self.assertFalse(receipt.move_id)
        self.assertNotEqual(receipt.state, "done")

    def test_equal_bases_make_a_swap_invisible_to_totals(self):
        """Why the rate check has to happen at construction.

        With both buckets at base 100, swapping the taxes posts exactly the
        amounts the receipt reports — 23.00 and 19.00 — so the document total,
        its total VAT and even the per-rate tax amounts all agree. Only the
        base attribution is wrong, and only on the VAT return.
        """
        receipt = self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Swapped", "issue_date": "2026-03-14 10:00:00",
            "amount_total": 242.00, "state": "captured",
            "tax_summary_ids": [
                fields.Command.create({"vat_rate": 23.0,
                                       "amount_untaxed": 100.0,
                                       "amount_tax": 23.0}),
                fields.Command.create({"vat_rate": 19.0,
                                       "amount_untaxed": 100.0,
                                       "amount_tax": 19.0}),
            ],
        })
        self.assertEqual(receipt.amount_tax, 42.0)
        self.assertFalse(receipt._check_reconciliation())
        receipt.action_create_partner()
        swapped = {23.0: self.tax_19, 19.0: self.tax_23}
        with patch.object(
                type(receipt), "_tax_for_rate",
                lambda self, rate: next(
                    (t for r, t in swapped.items() if abs(r - rate) < 0.001),
                    self.env["account.tax"])):
            # The construction check is the only thing that sees it.
            with self.assertRaisesRegex(UserError, "is mapped to"):
                receipt.action_create_bill()

    def test_tax_number_matches_a_vat_number_built_from_it(self):
        partner = self.env["res.partner"].create({
            "name": "Plain trader", "is_company": True, "vat": "SK2077000002",
        })
        receipt = self._fuel_receipt()
        receipt.seller_vat = False
        receipt.seller_reg_id = False
        self.assertEqual(receipt._find_partner(), partner)

    def test_a_longer_number_ending_the_same_way_does_not_match(self):
        """The old suffix match would have collided here."""
        self.env["res.partner"].create({
            "name": "Unrelated", "is_company": True, "vat": "SK99992077000002",
        })
        receipt = self._fuel_receipt()
        receipt.seller_vat = False
        receipt.seller_reg_id = False
        self.assertFalse(receipt._find_partner())

    def test_normalized_search_refuses_an_unexpected_column(self):
        """The column is interpolated into SQL, so it is whitelisted."""
        receipt = self._fuel_receipt()
        with self.assertRaises(ValueError):
            receipt._search_partner_by_normalized("name", "anything")

    # ------------------------------------------------------------------
    # dedup
    # ------------------------------------------------------------------
    def test_same_receipt_cannot_be_captured_twice(self):
        self._fuel_receipt()
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self._fuel_receipt()

    def test_uncaptured_receipts_do_not_collide(self):
        """Several receipts may sit without an identifier at once."""
        Receipt = self.env["cssk.receipt"]
        a = Receipt.create({"company_id": self.company.id,
                            "currency_id": self.company.currency_id.id})
        b = Receipt.create({"company_id": self.company.id,
                            "currency_id": self.company.currency_id.id})
        self.assertNotEqual(a, b)
        self.assertFalse(a.receipt_uid)
