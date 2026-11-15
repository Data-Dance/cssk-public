# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date

from odoo.tools.misc import format_date

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzAssetProtocol(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Vozidla",
                "journal_id": cls.company_data["default_journal_misc"].id,
                "account_asset_id": cls._account("022000").id,
                "account_depreciation_id": cls._account("082000").id,
                "account_expense_depreciation_id": cls._account("551000").id,
                "company_id": cls.company.id,
            }
        )
        cls.asset = cls.env["account.asset"].create(
            {
                "name": "Osobní automobil",
                "profile_id": cls.profile.id,
                "purchase_value": 600000.0,
                "date_start": "2026-01-15",
                "company_id": cls.company.id,
                "l10n_cz_inventory_number": "INV-2026-0007",
                "l10n_cz_location": "Praha, sídlo",
            }
        )

    @classmethod
    def _account(cls, code):
        account = cls.env["account.account"].search(
            [("company_ids", "in", cls.company.id), ("code", "=", code)], limit=1
        )
        # an empty account here would only surface as a missing required field
        assert account, "the Czech chart has no account %s" % code
        return account

    def _render(self, template, asset=None):
        return str(
            self.env["ir.qweb"]._render(
                "l10n_cz_asset_protocol_base.%s" % template,
                {"docs": asset or self.asset},
            )
        )

    def test_protocol_fields_live_on_the_register(self):
        self.assertEqual(self.asset.l10n_cz_inventory_number, "INV-2026-0007")
        self.assertEqual(self.asset.l10n_cz_location, "Praha, sídlo")

    def test_zarazovaci_protokol_renders(self):
        html = self._render("report_zarazovaci_protokol")
        self.assertIn("Protokol o zařazení", html)
        self.assertIn("§ 11", html)  # internal doklad, not a prescribed form
        self.assertIn("563/1991", html)
        self.assertIn("INV-2026-0007", html)
        self.assertIn("Osobní automobil", html)
        self.assertIn("Praha, sídlo", html)

    def test_vyrazovaci_protokol_renders_with_reason_and_method(self):
        self.asset.write(
            {
                "l10n_cz_disposal_method": "sale",
                "l10n_cz_disposal_reason": "Prodej třetí osobě.",
            }
        )
        html = self._render("report_vyrazovaci_protokol")
        self.assertIn("Protokol o vyřazení", html)
        self.assertIn("Prodej třetí osobě.", html)
        self.assertIn("přílohy", html)

    def test_disposal_method_prints_in_czech_in_any_language(self):
        """The protocol is a Czech document: the method is printed in the
        wording of ČÚS č. 013, bod 5.4, not as the interface label of the
        user's language."""
        from odoo.addons.l10n_cz_asset_protocol_base.models import (
            l10n_cz_asset_protocol_mixin as mixin,
        )

        selection = dict(
            self.env["account.asset"]._fields["l10n_cz_disposal_method"].selection
        )
        self.assertEqual(set(selection), set(mixin.DISPOSAL_METHOD_TERMS))
        self.asset.l10n_cz_disposal_method = "contribution"
        for lang in ("en_US", "cs_CZ"):
            html = self._render(
                "report_vyrazovaci_protokol", self.asset.with_context(lang=lang)
            )
            self.assertIn("vklad do jiné obchodní korporace", html)
        self.asset.l10n_cz_disposal_method = False
        self.assertEqual(self.asset._l10n_cz_protocol_values()["disposal_method"], "")

    def test_both_signature_records_of_par_11(self):
        """§ 11 odst. 1 písm. f) zákona č. 563/1991 Sb. asks for two
        podpisové záznamy: the person responsible for the účetní případ and
        the person responsible for posting it."""
        for template in ("report_zarazovaci_protokol", "report_vyrazovaci_protokol"):
            html = self._render(template)
            self.assertIn("Osoba odpovědná za účetní případ", html)
            self.assertIn("Osoba odpovědná za zaúčtování", html)

    def test_inventory_number_falls_back_to_the_register_code(self):
        self.asset.l10n_cz_inventory_number = False
        self.asset.code = "FA/0001"
        html = self._render("report_zarazovaci_protokol")
        self.assertIn("FA/0001", html)

    def test_print_actions_render_the_shared_templates(self):
        """What the Print menu runs: the report ACTION, not the template.

        An action naming a template of the wrong module fails on printing
        while the template-level tests above stay green.
        """
        for xmlid, title in (
            ("l10n_cz_asset_protocol_oca.action_report_zarazovaci_protokol",
             "Protokol o zařazení"),
            ("l10n_cz_asset_protocol_oca.action_report_vyrazovaci_protokol",
             "Protokol o vyřazení"),
        ):
            report = self.env.ref(xmlid)
            self.assertTrue(
                report.report_name.startswith("l10n_cz_asset_protocol_base."))
            html, _type = self.env["ir.actions.report"]._render_qweb_html(
                report, self.asset.ids)
            self.assertIn(title, html.decode())
            self.assertIn("INV-2026-0007", html.decode())

    def _asset_with_salvage(self):
        asset = self.env["account.asset"].create(
            {
                "name": "Stroj se zbytkovou hodnotou",
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
        would not give the printed zůstatková cena."""
        asset = self._asset_with_salvage()
        values = asset._l10n_cz_protocol_values()
        self.assertAlmostEqual(values["depreciated"], 5000.0, 2)  # (24 000 − 4 000) / 4
        self.assertAlmostEqual(values["residual"], 19000.0, 2)
        self.assertAlmostEqual(
            values["purchase_value"] - values["depreciated"], values["residual"], 2)

    def test_disposal_protocol_keeps_the_residual_written_off(self):
        """After removal OCA counts the removal line as depreciated, which
        would print oprávky of the whole base and a zůstatková cena of nil."""
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
        values = asset._l10n_cz_protocol_values()
        posted = sum(
            asset.depreciation_line_ids.filtered(
                lambda l: l.type == "depreciate" and (l.init_entry or l.move_check)
            ).mapped("amount")
        )
        self.assertAlmostEqual(values["depreciated"], posted, 2)
        self.assertLess(values["depreciated"], 20000.0)
        self.assertAlmostEqual(values["residual"], 24000.0 - posted, 2)
        self.assertGreater(values["residual"], 4000.0)
        self.assertEqual(str(values["disposal_date"]), "2025-06-30")

    def test_protocols_carry_number_and_date_of_making_out(self):
        """§ 11 odst. 1 písm. a) and d) zákona č. 563/1991 Sb."""
        self.asset.l10n_cz_commissioning_protocol_date = "2026-01-20"
        html = self._render("report_zarazovaci_protokol")
        self.assertIn("ZP-INV-2026-0007", html)
        self.assertIn("Datum vyhotovení", html)
        self.assertIn(format_date(self.env, date(2026, 1, 20)), html)
        html = self._render("report_vyrazovaci_protokol")
        self.assertIn("VP-INV-2026-0007", html)
        self.assertIn("Datum vyhotovení", html)

    def test_tax_group_rows_only_with_tax_depreciation(self):
        """Odpisová skupina and způsob daňového odpisování come from
        account_asset_tax, which the protocols do not depend on: without it
        (or without a Czech group on the asset) the rows are not printed."""
        asset = self.asset
        values = asset._l10n_cz_protocol_values()
        self.assertEqual(values["tax_group"], "")
        self.assertEqual(values["tax_method"], "")
        self.assertNotIn("Odpisová skupina", self._render("report_zarazovaci_protokol"))
        if "tax_class_id" not in asset._fields:
            return
        tax_class = self.env["account.asset.tax.class"].search(
            [("country_code", "=", "CZ"), ("group_number", "=", 2)], limit=1
        )
        if not tax_class:
            return
        asset.write(
            {
                "tax_depreciation_enabled": True,
                "tax_class_id": tax_class.id,
                "tax_method": "accelerated",
            }
        )
        values = asset._l10n_cz_protocol_values()
        self.assertEqual(values["tax_group"], "2")
        self.assertEqual(values["tax_method"], "zrychlené (§ 32)")
        html = self._render("report_zarazovaci_protokol")
        self.assertIn("Odpisová skupina", html)
        self.assertIn("zrychlené (§ 32)", html)
