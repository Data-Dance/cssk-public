# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkAssetProtocol(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Vozidlá",
                "journal_id": cls.company_data["default_journal_misc"].id,
                "account_asset_id": cls.env["account.account"]
                .search(
                    [("company_ids", "in", cls.company.id), ("code", "=", "022000")],
                    limit=1,
                )
                .id,
                "account_depreciation_id": cls.env["account.account"]
                .search(
                    [("company_ids", "in", cls.company.id), ("code", "=", "082000")],
                    limit=1,
                )
                .id,
                "account_expense_depreciation_id": cls.env["account.account"]
                .search(
                    [("company_ids", "in", cls.company.id), ("code", "=", "551000")],
                    limit=1,
                )
                .id,
                "company_id": cls.company.id,
            }
        )
        cls.asset = cls.env["account.asset"].create(
            {
                "name": "Osobné vozidlo",
                "profile_id": cls.profile.id,
                "purchase_value": 24000.0,
                "date_start": "2026-01-15",
                "company_id": cls.company.id,
                "l10n_sk_inventory_number": "INV-2026-0007",
                "l10n_sk_location": "Bratislava, sídlo",
            }
        )

    def test_protocol_fields_live_on_the_register(self):
        self.assertEqual(self.asset.l10n_sk_inventory_number, "INV-2026-0007")
        self.assertEqual(self.asset.l10n_sk_location, "Bratislava, sídlo")

    def test_zaradovaci_protokol_renders(self):
        html = str(
            self.env["ir.qweb"]._render(
                "l10n_sk_asset_protocol_base.report_zaradovaci_protokol",
                {"docs": self.asset},
            )
        )
        self.assertIn("Protokol o zaradení", html)
        self.assertIn("§ 10", html)  # internal doklad, not a prescribed form
        self.assertIn("INV-2026-0007", html)
        self.assertIn("Osobné vozidlo", html)

    def test_vyradovaci_protokol_renders_with_reason_and_method(self):
        self.asset.write(
            {
                "l10n_sk_disposal_method": "sale",
                "l10n_sk_disposal_reason": "Predaj tretej osobe.",
            }
        )
        html = str(
            self.env["ir.qweb"]._render(
                "l10n_sk_asset_protocol_base.report_vyradovaci_protokol",
                {"docs": self.asset},
            )
        )
        self.assertIn("Protokol o vyradení", html)
        self.assertIn("Predaj tretej osobe.", html)
        self.assertIn("prílohy", html)

    def test_inventory_number_falls_back_to_the_register_code(self):
        self.asset.l10n_sk_inventory_number = False
        self.asset.code = "FA/0001"
        html = str(
            self.env["ir.qweb"]._render(
                "l10n_sk_asset_protocol_base.report_zaradovaci_protokol",
                {"docs": self.asset},
            )
        )
        self.assertIn("FA/0001", html)
