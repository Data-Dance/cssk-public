# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""KH ↔ DPH, SH ↔ DPH and DPH ↔ ledger, all from the same posted data."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzReconciliation(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "CZ25663585", "city": "Praha"})
        cls.company.l10n_cssk_tax_authority_id = cls.env[
            "cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")],
            limit=1)
        cls.recon = cls.env["l10n.cz.dph.reconciliation"]
        ref = cls.env["account.chart.template"].ref
        cls.sale21 = ref("l10n_cz_21_domestic_supplies")
        cls.purchase21 = ref("l10n_cz_21_receipt_domestic_supplies")
        cls.eu_goods = ref("l10n_cz_supply_goods_eu")
        cls.eu_service = ref("l10n_cz_supply_service_eu")
        cls.rc_purchase = ref("l10n_cz_21_tax_reverse_charge_scheme")
        cls.cz_partner = cls.env["res.partner"].create({
            "name": "Odběratel s.r.o.", "vat": "CZ46342958",
            "country_id": cls.env.ref("base.cz").id})
        cls.eu_partner = cls.env["res.partner"].create({
            "name": "Kunde BE", "vat": "BE0477472701",
            "country_id": cls.env.ref("base.be").id})

    def _doc(self, move_type, partner, tax, amount, on="2025-05-15"):
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": partner.id,
            "invoice_date": on, "date": on, "taxable_supply_date": on,
            "ref": "%s-%s-%s" % (move_type, on, amount),
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        move.action_post()
        return move

    def _month(self):
        self._doc("out_invoice", self.cz_partner, self.sale21, 20000.0)
        self._doc("out_invoice", self.cz_partner, self.sale21, 3000.0)
        self._doc("in_invoice", self.cz_partner, self.purchase21, 30000.0)
        self._doc("in_invoice", self.cz_partner, self.rc_purchase, 8000.0)
        self._doc("out_invoice", self.eu_partner, self.eu_goods, 50000.0)
        self._doc("out_invoice", self.eu_partner, self.eu_service, 7000.0)

    def _return(self, date_from="2025-05-01", date_to="2025-05-31",
                period="month"):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_version_2025").id,
            "statement_type_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_type_B").id,
            "period_type": period,
            "date_from": date_from, "date_to": date_to})
        ret.action_compute_lines()
        return ret

    def _kh(self, date_from="2025-05-01", date_to="2025-05-31"):
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_cz_kh.cz_kh_version_2025").id,
            "statement_type_id": self.env.ref("l10n_cz_kh.cz_kh_type_B").id,
            "period_type": "month",
            "date_from": date_from, "date_to": date_to})
        st.action_compute_lines()
        return st

    def _sh(self, date_from="2025-05-01", date_to="2025-05-31"):
        version = self.env.ref("l10n_cz_ec_sales.dphshv_version_2025")
        st = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "statement_type_id": version.statement_type_ids[0].id,
            "period_type": "month",
            "date_from": date_from, "date_to": date_to})
        st.action_compute_lines()
        return st

    def _by_code(self, rows):
        return {row["code"]: row for row in rows}

    # ------------------------------------------------------------------
    def test_the_control_rows_agree_on_clean_books(self):
        """Věta C of DPHKH1 against the rows the structure names."""
        self._month()
        rows = self._by_code(self.recon.reconcile_kh(self._kh(), self._return()))
        self.assertEqual(set(rows), {
            "obrat23", "obrat5", "pln23", "pln5", "pln_rez_pren",
            "rez_pren23", "rez_pren5", "celk_zd_a2"})
        self.assertEqual(rows["obrat23"]["filed"], 23000.0)
        self.assertEqual(rows["obrat23"]["computed"], 23000.0)
        self.assertEqual(rows["pln23"]["filed"], 30000.0)
        self.assertEqual(rows["rez_pren23"]["filed"], 8000.0)
        self.assertEqual(rows["rez_pren23"]["computed"], 8000.0)
        for code, row in rows.items():
            self.assertEqual(row["kind"], "ok", code)
            self.assertFalse(row["detail"], code)

    def test_a_difference_above_the_official_tolerance_is_reported(self):
        """"Výpočet s maximální tolerancí +/- 1000 Kč"."""
        self._month()
        kh, ret = self._kh(), self._return()
        line = ret.line_ids.filtered(lambda l: l.code == "obrat23")
        line.value = 23000.0 + 1000.0
        rows = self._by_code(self.recon.reconcile_kh(kh, ret))
        self.assertEqual(rows["obrat23"]["kind"], "ok", "within 1 000 Kč")
        line.value = 23000.0 + 1001.0
        rows = self._by_code(self.recon.reconcile_kh(kh, ret))
        self.assertEqual(rows["obrat23"]["kind"], "amount")
        self.assertEqual(rows["obrat23"]["diff"], -1001.0)
        self.assertTrue(rows["obrat23"]["detail"])
        self.assertEqual(rows["pln23"]["kind"], "ok")

    def test_a_quarterly_payer_adds_three_statements(self):
        """"Nebo součet tří kontrolních hlášení u čtvrtletního plátce"."""
        self._doc("out_invoice", self.cz_partner, self.sale21, 20000.0,
                  on="2025-04-10")
        self._doc("out_invoice", self.cz_partner, self.sale21, 15000.0,
                  on="2025-05-10")
        self._doc("out_invoice", self.cz_partner, self.sale21, 12000.0,
                  on="2025-06-10")
        ret = self._return("2025-04-01", "2025-06-30", period="quarter")
        may = self._kh()
        self.assertEqual(self.recon.find_vat_return(may), ret)
        rows = self._by_code(self.recon.reconcile_kh(may, ret))
        self.assertEqual(rows["obrat23"]["kind"], "info",
                         "two of the three statements are missing")
        self.assertIn("not compared", rows["obrat23"]["detail"])
        self._kh("2025-04-01", "2025-04-30")
        self._kh("2025-06-01", "2025-06-30")
        rows = self._by_code(self.recon.reconcile_kh(may, ret))
        self.assertEqual(rows["obrat23"]["filed"], 47000.0)
        self.assertEqual(rows["obrat23"]["computed"], 47000.0)
        self.assertEqual(rows["obrat23"]["kind"], "ok")

    def test_the_ec_sales_list_agrees_with_rows_20_21_31(self):
        """The instructions of ř. 20, 21 and 31 of the přiznání."""
        self._month()
        sh, ret = self._sh(), self._return()
        rows = self._by_code(self.recon.reconcile_sh(sh, ret))
        self.assertEqual(rows["sh_goods"]["filed"], 50000.0)
        self.assertEqual(rows["sh_goods"]["computed"], 50000.0)
        self.assertEqual(rows["sh_services"]["filed"], 7000.0)
        self.assertEqual(rows["sh_triangular"]["filed"], 0.0)
        self.assertEqual({r["kind"] for r in rows.values()}, {"ok"})
        ret.line_ids.filtered(lambda l: l.code == "dod_zb").value = 40000.0
        rows = self._by_code(self.recon.reconcile_sh(sh, ret))
        self.assertEqual(rows["sh_goods"]["kind"], "amount")
        self.assertEqual(rows["sh_services"]["kind"], "ok")

    def test_the_return_agrees_with_account_343(self):
        """Reverse charge books its output and its deduction under one
        purchase tax; each leg must land on its own side."""
        self._month()
        rows = self._by_code(self.recon.reconcile_books(self._return()))
        # 23 000 × 21 % + the self-assessed 8 000 × 21 %
        self.assertEqual(rows["out_vat"]["computed"], 4830.0 + 1680.0)
        self.assertEqual(rows["in_vat"]["computed"], 6300.0 + 1680.0)
        self.assertEqual(rows["out_vat"]["kind"], "ok")
        self.assertEqual(rows["in_vat"]["kind"], "ok")
        self.assertEqual(rows["other_343"]["kind"], "info")
        self.assertEqual(rows["other_343"]["computed"], 0.0)
        self.assertEqual(rows["revenue"]["kind"], "info")

    def test_vat_booked_by_hand_shows(self):
        """Tax on 343 with no tax behind it is in no row of the return."""
        self._month()
        vat = self.env["account.account"].search([
            ("company_ids", "in", self.company.id),
            ("code", "=like", "343%")], limit=1)
        self.env["account.move"].create({
            "move_type": "entry", "date": "2025-05-20",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                Command.create({"account_id": vat.id, "credit": 500.0}),
                Command.create({
                    "account_id": self.company_data[
                        "default_account_expense"].id, "debit": 500.0})],
        }).action_post()
        rows = self._by_code(self.recon.reconcile_books(self._return()))
        self.assertEqual(rows["other_343"]["computed"], -500.0)
        self.assertTrue(rows["other_343"]["detail"])
        self.assertEqual(rows["out_vat"]["kind"], "ok")

    def test_a_typed_total_that_left_the_ledger_is_reported(self):
        self._month()
        ret = self._return()
        ret.line_ids.filtered(lambda l: l.code == "dan_zocelk").value = 9999.0
        rows = self._by_code(self.recon.reconcile_books(ret))
        self.assertEqual(rows["out_vat"]["kind"], "amount")
        self.assertTrue(rows["out_vat"]["detail"])

    def test_the_buttons_write_the_comparison(self):
        self._month()
        kh, sh = self._kh(), self._sh()
        with self.assertRaisesRegex(UserError, "No computed přiznání"):
            kh.action_l10n_cz_reconcile_dph()
        ret = self._return()
        for record, action, count in (
                (kh, "action_l10n_cz_reconcile_dph", 8),
                (sh, "action_l10n_cz_reconcile_dph", 3),
                (ret, "action_l10n_cz_reconcile_books", 4)):
            result = getattr(record, action)()
            self.assertEqual(result["type"], "ir.actions.act_window")
            found = self.env["cssk.filing.discrepancy"].search([
                ("res_model", "=", record._name), ("res_id", "=", record.id)])
            self.assertEqual(len(found), count, action)
