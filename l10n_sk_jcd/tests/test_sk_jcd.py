# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkJcd(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.customs = cls.env["res.partner"].create({"name": "Colný úrad Bratislava"})

    def _jcd(self, **overrides):
        vals = {
            "company_id": self.company.id,
            "customs_office_id": self.customs.id,
            "customs_value": 10000.0,
            "duty_amount": 500.0,
            "other_charges": 0.0,
            "vat_rate": "23",
            "vat_regime": "paid",
        }
        vals.update(overrides)
        return self.env["l10n.sk.jcd"].create(vals)

    def _confirm_customs_document(self, jcd):
        """MRN + an attached document — what § 49 ods. 2 písm. d) requires."""
        jcd.mrn = "24SK5810000123456X"
        self.env["ir.attachment"].create(
            {
                "name": "JCD potvrdená colným úradom.pdf",
                "res_model": jcd._name,
                "res_id": jcd.id,
                "raw": b"%PDF-1.4 test",
            }
        )
        jcd.invalidate_recordset(["customs_document_ok"])
        return jcd

    # ------------------------------------------------------------------
    def _historic_clone(self, current, rate, valid_from, valid_to):
        """A historical rate as the generator makes one: an archived clone."""
        clone = current.copy({"name": "%g%% historic" % rate, "amount": rate})
        clone.write({
            "cssk_historic_valid_from": valid_from,
            "cssk_historic_valid_to": valid_to,
            "cssk_historic_source_tax_id": current.id,
            "active": False,
        })
        return clone

    def _requires_historic_rates(self):
        if "cssk_historic_source_tax_id" not in self.env["account.tax"]._fields:
            self.skipTest("l10n_cssk_vat_return_base is not installed")

    def test_a_back_dated_declaration_is_taxed_at_the_rate_of_its_day(self):
        """The chart ships today's rates; a 2019 import was not taxed at them.

        The base is what the customs office assessed, so posting at the current
        rate moves only the tax figure — silently, and by three points.
        """
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2019-06-30")
        current = self.env.ref(
            "account.%s_vs_cust_23" % self.company.id, raise_if_not_found=False
        )
        self.assertTrue(current, "premise: the SK chart ships the 23 % import tax")
        self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")

        jcd.invalidate_recordset()
        self.assertEqual(jcd._get_import_tax().amount, 20.0)
        self.assertEqual(jcd.vat_rate_effective, 20.0)
        self.assertEqual(jcd.vat_amount, jcd.currency_id.round(jcd.vat_base * 0.20))

    def test_a_current_declaration_still_uses_the_current_rate(self):
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2026-06-30")
        current = self.env.ref("account.%s_vs_cust_23" % self.company.id)
        self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")

        jcd.invalidate_recordset()
        self.assertEqual(jcd._get_import_tax(), current)
        self.assertEqual(jcd.vat_rate_effective, 23.0)

    def test_the_shown_rate_and_the_posted_tax_cannot_disagree(self):
        """`vat_amount` reads the resolved tax, not the band's label.

        A document that displays one rate and posts another is worse than one
        that is simply wrong, because it looks checked.
        """
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2019-06-30")
        current = self.env.ref("account.%s_vs_cust_23" % self.company.id)
        self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")
        jcd.invalidate_recordset()

        self.assertEqual(jcd.vat_rate_effective, jcd._get_import_tax().amount)
        self.assertAlmostEqual(
            jcd.vat_amount,
            jcd.currency_id.round(
                jcd.vat_base * jcd.vat_rate_effective / 100.0),
            places=2,
        )

    def test_a_date_older_than_any_known_rate_keeps_the_current_one(self):
        """Slovak rates before 2011 are deliberately not cloned, so there is
        nothing to resolve to. Falling back to the band leaves the accountant
        where they were rather than failing to post at all."""
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2008-06-30")
        current = self.env.ref("account.%s_vs_cust_23" % self.company.id)
        self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")
        jcd.invalidate_recordset()
        self.assertEqual(jcd._get_import_tax(), current)

    def test_a_back_dated_declaration_POSTS_at_the_rate_of_its_day(self):
        """The one that matters: not what resolves, but what reaches the books.

        The historical rate is an ARCHIVED tax, and an archived tax on a posted
        move line is the part of this worth proving rather than assuming.
        """
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2019-06-30", duty_amount=0.0)
        current = self.env.ref("account.%s_vs_cust_23" % self.company.id)
        clone = self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")
        jcd.invalidate_recordset()
        self._confirm_customs_document(jcd)

        jcd.action_post()
        self.assertEqual(jcd.state, "posted")
        tax_lines = jcd.move_id.line_ids.filtered("tax_line_id")
        self.assertTrue(tax_lines, "the VAT must reach the ledger")
        self.assertEqual(tax_lines.tax_line_id, clone)
        self.assertAlmostEqual(
            sum(tax_lines.mapped("balance")), jcd.vat_amount, places=2)
        self.assertAlmostEqual(
            jcd.vat_amount,
            jcd.currency_id.round(jcd.vat_base * 0.20), places=2,
            msg="10 000 at 20 %, not 23 % — three points of a real assessment")

    def test_two_rates_of_one_band_on_one_day_refuse(self):
        """Overlapping windows would tax the same base two ways.

        Unlike interchangeable variants of a single rate, there is nothing to
        choose between them, so this says so instead of picking one.
        """
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2019-06-30")
        current = self.env.ref("account.%s_vs_cust_23" % self.company.id)
        self._historic_clone(current, 20.0, "2011-01-01", "2024-12-31")
        self._historic_clone(current, 19.0, "2004-01-01", "2020-12-31")
        jcd.invalidate_recordset()
        with self.assertRaises(UserError):
            jcd._get_import_tax()

    def test_posting_refuses_if_the_rate_moved_since_it_was_approved(self):
        """A stored figure and a live resolution can part company between
        entering a declaration and posting it."""
        self._requires_historic_rates()
        jcd = self._jcd(vat_rate="23", date="2026-06-30", duty_amount=0.0)
        self._confirm_customs_document(jcd)
        self.assertEqual(jcd.vat_rate_effective, 23.0)
        # The chart is corrected underneath a declaration already approved.
        self.env.ref("account.%s_vs_cust_23" % self.company.id).amount = 21.0
        with self.assertRaises(UserError):
            jcd.action_post()

    def test_a_band_that_is_not_a_band_names_itself(self):
        """A rate written straight into the database by an import is invalid
        selection data; a traceback is a worse answer than saying so."""
        jcd = self._jcd()
        self.env.cr.execute(
            "UPDATE l10n_sk_jcd SET vat_rate = '20' WHERE id = %s", (jcd.id,))
        jcd.invalidate_recordset()
        with self.assertRaises(UserError):
            jcd._get_import_tax()

    def test_clearing_account_wired_from_the_chart(self):
        self.assertEqual(
            self.company.l10n_sk_jcd_clearing_account_id.code, "379000"
        )

    def test_vat_base_defaults_to_customs_value_plus_duty_and_charges(self):
        jcd = self._jcd(other_charges=250.0)
        self.assertEqual(jcd.vat_base, 10750.0)
        self.assertEqual(jcd.vat_amount, 2472.50)

    def test_vat_base_is_overridable(self):
        """§ 24 has components a customs declaration alone does not know."""
        jcd = self._jcd()
        jcd.vat_base = 12000.0
        self.assertEqual(jcd.vat_amount, 2760.0)

    def test_deduction_is_gated_on_the_confirmed_customs_document(self):
        jcd = self._jcd()
        self.assertFalse(jcd.customs_document_ok)
        with self.assertRaisesRegex(UserError, "dovozného dokladu"):
            jcd.action_post()

        # MRN alone is not enough — the document itself must be there.
        jcd.mrn = "24SK5810000123456X"
        jcd.invalidate_recordset(["customs_document_ok"])
        self.assertFalse(jcd.customs_document_ok)

        self._confirm_customs_document(jcd)
        self.assertTrue(jcd.customs_document_ok)

    def test_paid_regime_selects_the_customs_tax(self):
        jcd = self._jcd(vat_regime="paid", vat_rate="23")
        self.assertEqual(jcd._get_import_tax().amount, 23.0)
        self.assertIn("CUST", jcd._get_import_tax().name)

    def test_postponed_regime_selects_the_84a_tax(self):
        jcd = self._jcd(vat_regime="postponed", vat_rate="19")
        tax = jcd._get_import_tax()
        self.assertEqual(tax.amount, 19.0)
        self.assertIn("IMP POST", tax.name)

    def test_posting_leaves_only_vat_and_duty_real(self):
        """The notional base nets to zero on the clearing account."""
        jcd = self._confirm_customs_document(self._jcd())
        jcd.action_post()

        self.assertEqual(jcd.state, "posted")
        move = jcd.move_id
        self.assertEqual(move.state, "posted")

        clearing = self.company.l10n_sk_jcd_clearing_account_id
        clearing_balance = sum(
            move.line_ids.filtered(lambda l: l.account_id == clearing).mapped("balance")
        )
        self.assertEqual(
            clearing_balance, 0.0, "the notional import base must net to zero"
        )
        # What the customs office is actually owed: VAT + duty.
        payable = sum(
            move.line_ids.filtered(
                lambda l: l.account_id.account_type == "liability_payable"
            ).mapped("balance")
        )
        self.assertEqual(abs(payable), jcd.vat_amount + jcd.duty_amount)

    def test_posted_vat_lands_on_the_deduction_rows(self):
        """r23 for 23 % paid to customs — the row the poučenie bod 38 names."""
        jcd = self._confirm_customs_document(self._jcd())
        jcd.action_post()

        tax_lines = jcd.move_id.line_ids.filtered("tax_line_id")
        self.assertTrue(tax_lines)
        # Exactly r23, not r23a/b/c (those are the § 84a deduction rows) and not
        # r22/r22a (the other rates). The tag set is the assertion.
        self.assertEqual(set(tax_lines.mapped("tax_tag_ids.name")), {"23"})
        self.assertEqual(sum(tax_lines.mapped("balance")), jcd.vat_amount)

        # And the notional base reaches no row at all: vs_cust_* base
        # repartition carries no tag (poučenie bod 38 — only the tax is reported).
        base_lines = jcd.move_id.line_ids.filtered(
            lambda line: line.tax_ids and not line.tax_line_id
        )
        self.assertTrue(base_lines)
        self.assertFalse(base_lines.mapped("tax_tag_ids"))

    def test_postponed_regime_reports_base_and_both_tax_rows(self):
        """§ 84a ods. 3: base on r11e, tax +r23c / -r12e, nothing payable."""
        jcd = self._confirm_customs_document(
            self._jcd(vat_regime="postponed", vat_rate="23", duty_amount=0.0)
        )
        jcd.action_post()

        move = jcd.move_id
        base_lines = move.line_ids.filtered(
            lambda line: line.tax_ids and not line.tax_line_id
        )
        self.assertEqual(set(base_lines.mapped("tax_tag_ids.name")), {"11e"})
        self.assertEqual(
            set(move.line_ids.filtered("tax_line_id").mapped("tax_tag_ids.name")),
            {"23c", "12e"},
        )
        # Self-assessed: the two tax legs cancel, so nothing is owed.
        self.assertEqual(
            sum(move.line_ids.filtered("tax_line_id").mapped("balance")), 0.0
        )

    def test_duty_is_billed_to_the_account_the_landed_cost_credits(self):
        """Copilot review: different accounts would double-count the duty.

        The bill debits the duty as an expense; validating the landed cost
        credits it back and debits stock. Same account on both legs or the duty
        is counted twice in the P&L.
        """
        jcd = self._confirm_customs_document(self._jcd())
        expected = jcd._duty_expense_account()
        self.assertTrue(expected)
        jcd.action_post()

        duty_lines = jcd.move_id.line_ids.filtered(
            lambda line: line.account_id == expected and line.debit
        )
        self.assertTrue(duty_lines, "the duty must be billed to that account")
        self.assertEqual(sum(duty_lines.mapped("debit")), jcd.duty_amount)

    def test_a_posted_declaration_is_not_silently_unwound(self):
        jcd = self._confirm_customs_document(self._jcd())
        jcd.action_post()
        with self.assertRaisesRegex(UserError, "Reverse the posted document"):
            jcd.action_cancel()

    def test_duty_is_capitalised_into_the_stock_value(self):
        """The headline: clo raises the landed cost of the goods received."""
        # Landed costs are only allowed on FIFO/AVCO categories — Odoo refuses
        # them on standard costing, which is a real constraint on this feature.
        category = self.env["product.category"].create(
            {"name": "Dovoz FIFO", "property_cost_method": "fifo"}
        )
        product = self.env["product.product"].create(
            {
                "name": "Dovezený tovar",
                "is_storable": True,
                "standard_price": 100.0,
                "categ_id": category.id,
            }
        )
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("company_id", "=", self.company.id)], limit=1
        )
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "partner_id": self.customs.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "company_id": self.company.id,
                "move_ids": [
                    Command.create(
                        {
                            # stock.move has no `name` in 19.0 (_rec_name = 'reference')
                            "product_id": product.id,
                            "product_uom_qty": 10.0,
                            "location_id": self.env.ref(
                                "stock.stock_location_suppliers"
                            ).id,
                            "location_dest_id": picking_type.default_location_dest_id.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        jcd = self._confirm_customs_document(
            self._jcd(duty_amount=500.0, picking_ids=[Command.set(picking.ids)])
        )
        jcd.action_post()

        landed = jcd.landed_cost_id
        self.assertTrue(landed, "a landed cost must carry the duty into stock")
        # Pinned to the same account the bill debited.
        self.assertEqual(
            landed.cost_lines.account_id, jcd._duty_expense_account()
        )
        self.assertEqual(landed.amount_total, 500.0)
        self.assertEqual(landed.picking_ids, picking)
        # computed, so the duty is actually allocated to the received goods
        self.assertTrue(landed.valuation_adjustment_lines)
        self.assertEqual(
            sum(landed.valuation_adjustment_lines.mapped("additional_landed_cost")),
            500.0,
        )

    def test_zero_base_is_refused(self):
        jcd = self._confirm_customs_document(
            self._jcd(customs_value=0.0, duty_amount=0.0)
        )
        with self.assertRaisesRegex(UserError, "zero"):
            jcd.action_post()
