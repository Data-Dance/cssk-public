# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tools.misc import format_date

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

    def test_print_actions_render_the_shared_templates(self):
        """What the Print menu runs: the report ACTION, not the template.

        The actions used to name ``l10n_sk_asset_protocol.*`` — a module that
        no longer exists — so printing failed on Community while the
        template-level tests above stayed green.
        """
        for xmlid, title in (
            ("l10n_sk_asset_protocol_oca.action_report_zaradovaci_protokol",
             "Protokol o zaradení"),
            ("l10n_sk_asset_protocol_oca.action_report_vyradovaci_protokol",
             "Protokol o vyradení"),
        ):
            report = self.env.ref(xmlid)
            self.assertTrue(
                report.report_name.startswith("l10n_sk_asset_protocol_base."))
            html, _type = self.env["ir.actions.report"]._render_qweb_html(
                report, self.asset.ids)
            self.assertIn(title, html.decode())
            self.assertIn("INV-2026-0007", html.decode())

    def _asset_with_salvage(self):
        asset = self.env["account.asset"].create(
            {
                "name": "Stroj so zostatkom",
                "profile_id": self.profile.id,
                "purchase_value": 24000.0,
                "salvage_value": 4000.0,
                "date_start": "2024-01-01",
                "method_time": "year",
                "method_number": 4,
                "method_period": "year",
                "prorata": False,
                "company_id": self.company.id,
            }
        )
        asset.compute_depreciation_board()
        asset.validate()
        asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and l.line_date.year == 2024
        ).create_move()
        asset.invalidate_recordset()
        return asset

    def test_protocol_amounts_foot_with_a_salvage_value(self):
        """OCA's residual leaves out the salvage value, so purchase − oprávky
        did not give the printed zostatková cena."""
        asset = self._asset_with_salvage()
        values = asset._l10n_sk_protocol_values()
        self.assertAlmostEqual(values["depreciated"], 5000.0, 2)  # (24 000 − 4 000) / 4
        self.assertAlmostEqual(values["residual"], 19000.0, 2)
        self.assertAlmostEqual(
            values["purchase_value"] - values["depreciated"], values["residual"], 2)

    def test_disposal_protocol_keeps_the_residual_written_off(self):
        """After removal OCA counts the removal line as depreciated, which
        printed oprávky of the whole base and a zostatková cena of nil."""
        asset = self._asset_with_salvage()
        wiz = self.env["account.asset.remove"].with_context(
            active_id=asset.id, early_removal=True
        ).create(
            {
                "date_remove": "2025-06-30",
                "sale_value": 0.0,
                "posting_regime": "gain_loss_on_sale",
                "account_plus_value_id": self.company_data["default_account_revenue"].id,
                "account_min_value_id": self.company_data["default_account_expense"].id,
            }
        )
        wiz.remove()
        asset.invalidate_recordset()
        self.assertEqual(asset.state, "removed")
        values = asset._l10n_sk_protocol_values()
        posted = sum(
            asset.depreciation_line_ids.filtered(
                lambda l: l.type == "depreciate" and (l.init_entry or l.move_check)
            ).mapped("amount")
        )
        self.assertAlmostEqual(values["depreciated"], posted, 2)
        self.assertLess(values["depreciated"], 20000.0)
        self.assertAlmostEqual(values["residual"], 24000.0 - posted, 2)
        self.assertGreater(values["residual"], 4000.0)

    def test_protocols_carry_number_and_date_of_making_out(self):
        """§ 10 ods. 1 písm. a) and d) zákona 431/2002."""
        self.asset.l10n_sk_commissioning_protocol_date = "2026-01-20"
        html = str(
            self.env["ir.qweb"]._render(
                "l10n_sk_asset_protocol_base.report_zaradovaci_protokol",
                {"docs": self.asset},
            )
        )
        self.assertIn("ZP-INV-2026-0007", html)
        self.assertIn("Dátum vyhotovenia", html)
        self.assertIn(format_date(self.env, date(2026, 1, 20)), html)
        html = str(
            self.env["ir.qweb"]._render(
                "l10n_sk_asset_protocol_base.report_vyradovaci_protokol",
                {"docs": self.asset},
            )
        )
        self.assertIn("VP-INV-2026-0007", html)
        self.assertIn("Dátum vyhotovenia", html)
