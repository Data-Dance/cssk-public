# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

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
        self.assertEqual(self.company.l10n_sk_fuel_income_ratio, 80.0)
        self.assertEqual(self.nondeductible.code, "548000")
        # § 85n fixes the VAT share at 50 %, in the tax repartition. A setting
        # for it existed once and changed nothing; it must not come back.
        self.assertNotIn("l10n_sk_vehicle_vat_ratio", self.company._fields)
        for xmlid in ("vs_auto_23", "vs_auto_19"):
            tax = self.env.ref(f"account.{self.company.id}_{xmlid}")
            self.assertEqual(
                tax.invoice_repartition_line_ids.filtered(
                    lambda line: line.repartition_type == "tax"
                ).mapped("factor_percent"),
                [50.0, 50.0],
            )

    def test_19_percent_vehicle_tax_deducts_on_the_19_percent_account(self):
        """vs_auto_19 books like Odoo's own 19 % purchase tax (343110)."""
        stock = self.env.ref(f"account.{self.company.id}_vs_tuz_19")
        vehicle = self.env.ref(f"account.{self.company.id}_vs_auto_19")
        for document_type in ("invoice", "refund"):
            stock_account = stock.repartition_line_ids.filtered(
                lambda line, dt=document_type: line.repartition_type == "tax"
                and line.document_type == dt
            ).account_id
            deducted = vehicle.repartition_line_ids.filtered(
                lambda line, dt=document_type: line.repartition_type == "tax"
                and line.document_type == dt
                and line.account_id != self.nondeductible
            ).account_id
            self.assertEqual(stock_account.code, "343110")
            self.assertEqual(deducted, stock_account)

    def test_upgrade_moves_the_19_percent_tax_off_343120(self):
        """Companies created before 19.0.1.1.0 carry 343120 on vs_auto_19."""
        Chart = self.env["account.chart.template"]
        wrong = Chart.with_company(self.company).ref("chart_sk_343120")
        vehicle = self.env.ref(f"account.{self.company.id}_vs_auto_19")
        deducted = vehicle.repartition_line_ids.filtered(
            lambda line: line.account_id.code == "343110"
        )
        self.assertEqual(len(deducted), 2)
        deducted.account_id = wrong

        self.assertEqual(Chart._l10n_sk_vehicle_fix_19_account(self.company), 2)
        self.assertEqual(
            set(deducted.mapped("account_id.code")), {"343110"}
        )
        self.assertEqual(Chart._l10n_sk_vehicle_fix_19_account(self.company), 0)

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

    def test_split_keeps_the_total_of_a_tax_included_line(self):
        """A price-included tax: price_unit is gross, and so must the split be.

        Splitting the net subtotal and writing it back as a gross price_unit
        took the VAT out a second time: 123.00 became 100.00.
        """
        tax = self.tax.copy({"price_include_override": "tax_included"})
        bill = self._bill(net=123.0, tax=tax)
        self.assertEqual(bill.amount_total, 123.0)
        self.assertEqual(bill.invoice_line_ids.price_subtotal, 100.0)

        self.env["l10n.sk.fuel.split"].create(
            {
                "move_id": bill.id,
                "line_ids": [Command.set(bill.invoice_line_ids.ids)],
                "nondeductible_account_id": self.nondeductible.id,
            }
        ).action_split()

        self.assertEqual(bill.amount_total, 123.0, "totals must not move")
        self.assertEqual(bill.amount_untaxed, 100.0)
        by_account = {
            line.account_id: line.price_subtotal for line in bill.invoice_line_ids
        }
        self.assertAlmostEqual(by_account[self.nondeductible], 20.0, places=2)
        self.assertEqual(sum(bill.invoice_line_ids.mapped("price_total")), 123.0)

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

    # -- companies whose chart predates the module ---------------------
    def _drop_vehicle_taxes(self):
        for xmlid in ("vs_auto_23", "vs_auto_19"):
            self.env.ref(f"account.{self.company.id}_{xmlid}").unlink()

    def test_install_hook_creates_the_taxes_on_an_existing_company(self):
        """The taxes are @template data, which only a chart load applies.

        Unlinking them puts this company where every company is whose chart
        was loaded before the module: the hook must create them, not only
        wire the account.
        """
        from ..hooks import post_init_hook

        self._drop_vehicle_taxes()
        post_init_hook(self.env)

        for xmlid, deduction_account in (
            ("vs_auto_23", "343120"),
            ("vs_auto_19", "343110"),
        ):
            tax = self.env.ref(
                f"account.{self.company.id}_{xmlid}", raise_if_not_found=False
            )
            self.assertTrue(tax, f"{xmlid} was not created")
            self.assertEqual(tax.company_id, self.company)
            self.assertEqual(len(tax.repartition_line_ids), 6)
            tax_lines = tax.invoice_repartition_line_ids.filtered(
                lambda line: line.repartition_type == "tax"
            )
            self.assertEqual(
                sorted(tax_lines.mapped("account_id.code")),
                sorted([deduction_account, "548000"]),
            )
            self.assertEqual(tax_lines.mapped("factor_percent"), [50.0, 50.0])

    def test_reloading_never_duplicates_a_tax_that_exists(self):
        Chart = self.env["account.chart.template"]
        self.assertEqual(Chart._l10n_sk_vehicle_load_taxes(self.company), 0)
        self.env.ref(f"account.{self.company.id}_vs_auto_19").unlink()
        self.assertEqual(Chart._l10n_sk_vehicle_load_taxes(self.company), 1)
        self.assertEqual(Chart._l10n_sk_vehicle_load_taxes(self.company), 0)
        self.assertEqual(
            len(self.env.ref(f"account.{self.company.id}_vs_auto_23")
                .repartition_line_ids),
            6,
            "an existing tax must not get its repartition lines appended again",
        )
        self.assertEqual(
            self.env["account.tax"].search_count([
                ("company_id", "=", self.company.id),
                ("amount", "in", (23.0, 19.0)),
                ("type_tax_use", "=", "purchase"),
                ("invoice_repartition_line_ids.account_id", "=",
                 self.nondeductible.id),
            ]),
            2,
        )

    def test_a_company_missing_an_account_is_skipped_not_fatal(self):
        """One broken chart must not abort the install for every company."""
        self._drop_vehicle_taxes()
        Chart = self.env["account.chart.template"]
        # Stand-in for a chart the taxes cannot be loaded into (a deleted
        # account or tax group); patched on the registry class, which is the
        # one the loader's recordset belongs to.
        with patch.object(
            type(Chart), "_load_data", side_effect=ValueError("broken chart")
        ), self.assertLogs(
            "odoo.addons.l10n_sk_vehicle_expense.models.account_chart_template",
            level="WARNING",
        ):
            self.assertEqual(Chart._l10n_sk_vehicle_load_taxes(self.company), 0)
