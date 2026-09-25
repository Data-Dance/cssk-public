# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkVehicleExpense(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.tax = cls.env.ref(f"account.{cls.company.id}_vs_auto_23")
        cls.nondeductible = cls.company.l10n_sk_vehicle_nondeductible_account_id

    def _bill(self, net=100.0, tax=None):
        return self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-31",
                "company_id": self.company.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "PHL",
                            "quantity": 1.0,
                            "price_unit": net,
                            "tax_ids": [Command.set((tax or self.tax).ids)],
                        }
                    )
                ],
            }
        )

    # -- the VAT half: § 85n, in the tax repartition -------------------
    def test_defaults_are_the_two_statutory_ratios(self):
        self.assertEqual(self.company.l10n_sk_vehicle_vat_ratio, 50.0)
        self.assertEqual(self.company.l10n_sk_fuel_income_ratio, 80.0)
        self.assertEqual(self.nondeductible.code, "548000")

    def test_only_half_the_vat_is_deducted(self):
        bill = self._bill(net=100.0)
        bill.action_post()

        vat_lines = bill.line_ids.filtered("tax_line_id")
        deductible = vat_lines.filtered(
            lambda line: line.account_id.code.startswith("343")
        )
        lost = vat_lines.filtered(lambda line: line.account_id == self.nondeductible)
        self.assertEqual(sum(deductible.mapped("balance")), 11.50)
        self.assertEqual(sum(lost.mapped("balance")), 11.50)
        # The supplier still charged the full 23 %.
        self.assertEqual(bill.amount_total, 123.0)

    def test_only_the_deducted_half_is_reported_on_the_return(self):
        """The whole point of doing this in the repartition."""
        bill = self._bill(net=100.0)
        bill.action_post()

        vat_lines = bill.line_ids.filtered("tax_line_id")
        tagged_lines = vat_lines.filtered(lambda line: line.tax_tag_ids)
        self.assertEqual(set(tagged_lines.mapped("tax_tag_ids.name")), {"21"})
        self.assertEqual(sum(tagged_lines.mapped("balance")), 11.50)
        # The lost half carries no tag, so it reaches no row of the DPH return.
        untagged = vat_lines - tagged_lines
        self.assertEqual(untagged.account_id, self.nondeductible)
        self.assertFalse(untagged.tax_tag_ids)

    # -- the income-tax half: § 19 ods. 2 písm. l), in the wizard -------
    def test_fuel_split_moves_the_non_tax_share_without_changing_totals(self):
        bill = self._bill(net=100.0)
        before_total = bill.amount_total

        wizard = self.env["l10n.sk.fuel.split"].create(
            {
                "move_id": bill.id,
                "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                "nondeductible_account_id": self.nondeductible.id,
            }
        )
        self.assertEqual(wizard.income_ratio, 80.0)
        wizard.action_split()

        self.assertEqual(bill.amount_total, before_total, "totals must not move")
        by_account = {
            line.account_id: line.price_subtotal for line in bill.invoice_line_ids
        }
        self.assertEqual(by_account[self.nondeductible], 20.0)
        self.assertEqual(sum(bill.invoice_line_ids.mapped("price_subtotal")), 100.0)

    def test_fuel_split_keeps_the_vat_treatment_on_both_parts(self):
        """Reclassifying the expense must not change what VAT was charged."""
        bill = self._bill(net=100.0)
        self.env["l10n.sk.fuel.split"].create(
            {
                "move_id": bill.id,
                "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                "nondeductible_account_id": self.nondeductible.id,
            }
        ).action_split()
        bill.action_post()

        for line in bill.invoice_line_ids:
            self.assertEqual(line.tax_ids, self.tax)
        self.assertEqual(bill.amount_total, 123.0)
        deductible = bill.line_ids.filtered(
            lambda line: line.tax_line_id and line.tax_tag_ids
        )
        self.assertEqual(sum(deductible.mapped("balance")), 11.50)

    def test_split_respects_a_discount_instead_of_reapplying_it(self):
        """price_subtotal is already net of the discount — Copilot review."""
        bill = self._bill(net=200.0)
        bill.invoice_line_ids.discount = 50.0  # subtotal becomes 100.00
        self.assertEqual(bill.invoice_line_ids.price_subtotal, 100.0)

        self.env["l10n.sk.fuel.split"].create(
            {
                "move_id": bill.id,
                "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                "nondeductible_account_id": self.nondeductible.id,
            }
        ).action_split()

        by_account = {
            line.account_id: line.price_subtotal for line in bill.invoice_line_ids
        }
        self.assertEqual(by_account[self.nondeductible], 20.0)
        self.assertEqual(sum(bill.invoice_line_ids.mapped("price_subtotal")), 100.0)
        self.assertFalse(any(bill.invoice_line_ids.mapped("discount")))

    def test_splitting_twice_is_refused(self):
        """Compounding the reclassification would be silent — Copilot review."""
        bill = self._bill(net=100.0)
        wizard_vals = {
            "move_id": bill.id,
            "line_ids": [Command.set(bill.invoice_line_ids.ids)],
            "nondeductible_account_id": self.nondeductible.id,
        }
        self.env["l10n.sk.fuel.split"].create(dict(wizard_vals)).action_split()
        self.assertTrue(all(bill.invoice_line_ids.mapped("l10n_sk_fuel_split_done")))

        with self.assertRaisesRegex(UserError, "already been split"):
            self.env["l10n.sk.fuel.split"].create(
                {
                    "move_id": bill.id,
                    "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                    "nondeductible_account_id": self.nondeductible.id,
                }
            ).action_split()

    def test_split_ratio_is_configurable(self):
        bill = self._bill(net=100.0)
        self.env["l10n.sk.fuel.split"].create(
            {
                "move_id": bill.id,
                "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                "income_ratio": 50.0,
                "nondeductible_account_id": self.nondeductible.id,
            }
        ).action_split()
        by_account = {
            line.account_id: line.price_subtotal for line in bill.invoice_line_ids
        }
        self.assertEqual(by_account[self.nondeductible], 50.0)
