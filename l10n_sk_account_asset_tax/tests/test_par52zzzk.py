# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""§ 52zzzk ZDP: the VAT § 85n leaves undeducted on a passenger car is in its
accounting cost and out of its tax entry price.

Runs on whichever asset register is installed (OCA or Odoo Assets), and only
with ``l10n_sk_vehicle_expense``, which ships the taxes.
"""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


class _Par52zzzkCommon(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        if "l10n_sk_par85n" not in cls.env["account.tax"]._fields:
            cls.skipTest(cls, "l10n_sk_vehicle_expense is not installed")
        cls.company = cls.company_data["company"]
        cid = cls.company.id
        cls.tax_asset = cls.env.ref(f"account.{cid}_vs_auto_23_asset")
        cls.tax_running = cls.env.ref(f"account.{cid}_vs_auto_23")
        cls.tax_full = cls.env.ref(f"account.{cid}_vs_tuz_23")
        cls.acc_car = cls.env["account.account"].create({
            "code": "022100", "name": "Osobné automobily",
            "account_type": "asset_fixed",
            "company_ids": [Command.link(cid)],
        })

    def _bill(self, tax, account=None, net=20000.0, **line_vals):
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-03-10",
            "ref": "FA-CAR-1",
            "invoice_line_ids": [Command.create({
                "name": "Osobný automobil",
                "account_id": (account or self.acc_car).id,
                "quantity": 1.0, "price_unit": net,
                "tax_ids": [Command.set(tax.ids)],
                **line_vals,
            })],
        })
        bill.action_post()
        return bill


@tagged("post_install", "-at_install")
class TestPar52zzzkBooking(_Par52zzzkCommon):
    def test_the_undeducted_half_is_capitalised_on_the_asset_account(self):
        bill = self._bill(self.tax_asset)
        on_car = bill.line_ids.filtered(lambda l: l.account_id == self.acc_car)
        self.assertAlmostEqual(sum(on_car.mapped("balance")), 22300.0, 2)
        vat = bill.line_ids.filtered("tax_line_id")
        tagged_vat = vat.filtered("tax_tag_ids")
        self.assertAlmostEqual(sum(tagged_vat.mapped("balance")), 2300.0, 2,
                               msg="only the deducted half reaches the return")
        self.assertEqual(bill.amount_total, 24600.0)


@tagged("post_install", "-at_install")
class TestPar52zzzkOCA(_Par52zzzkCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "account.asset.profile" not in cls.env:
            cls.skipTest(cls, "the OCA asset register is not installed")
        journal = cls.company_data["default_journal_misc"]
        cls.profile = cls.env["account.asset.profile"].create({
            "name": "Osobné automobily",
            "journal_id": journal.id,
            "account_asset_id": cls.acc_car.id,
            "account_depreciation_id": cls.env["account.account"].create({
                "code": "082100", "name": "Oprávky k automobilom",
                "account_type": "asset_fixed",
                "company_ids": [Command.link(cls.company.id)],
            }).id,
            "account_expense_depreciation_id":
                cls.company_data["default_account_expense"].id,
            "method_time": "year", "method_number": 4, "method_period": "year",
        })

    def _car(self, tax):
        bill = self._bill(tax, asset_profile_id=self.profile.id)
        return bill.invoice_line_ids.asset_id

    def test_the_asset_costs_what_the_asset_account_holds(self):
        car = self._car(self.tax_asset)
        self.assertEqual(len(car), 1)
        self.assertAlmostEqual(car.purchase_value, 22300.0, 2)

    def test_the_tax_entry_price_leaves_the_vat_out(self):
        car = self._car(self.tax_asset)
        self.assertAlmostEqual(car._tax_entry_value_excluded(), 2300.0, 2)
        self.assertAlmostEqual(car._tax_default_entry_value(), 20000.0, 2)

    def test_a_fully_deducted_purchase_excludes_nothing(self):
        car = self._car(self.tax_full)
        self.assertAlmostEqual(car.purchase_value, 20000.0, 2)
        self.assertEqual(car._tax_entry_value_excluded(), 0.0)


@tagged("post_install", "-at_install")
class TestPar52zzzkEE(_Par52zzzkCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "original_move_line_ids" not in cls.env["account.asset"]._fields:
            cls.skipTest(cls, "Odoo Assets is not installed")
        cls.acc_car.create_asset = "draft"

    def _car(self, tax):
        bill = self._bill(tax)
        return bill.asset_ids

    def test_the_asset_costs_what_the_asset_account_holds(self):
        car = self._car(self.tax_asset)
        self.assertEqual(len(car), 1)
        self.assertAlmostEqual(car.original_value, 22300.0, 2)

    def test_vat_booked_to_an_expense_is_not_added_to_the_asset(self):
        """The running-cost tax puts the undeducted half on 548000; Odoo
        Assets used to add it to the asset as well."""
        car = self._car(self.tax_running)
        self.assertAlmostEqual(car.original_value, 20000.0, 2)

    def test_the_tax_entry_price_leaves_the_vat_out(self):
        car = self._car(self.tax_asset)
        self.assertAlmostEqual(car._tax_default_entry_value(), 20000.0, 2)
