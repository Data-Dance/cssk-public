# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkInterDocRecon(AccountTestInvoicingCommon):
    """SV ↔ DPH priznanie and VZS → DPPO cross-form reconciliations, all built
    from the same posted SK data."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava",
                           "country_id": cls.env.ref("base.sk").id})
        cls.recon = cls.env["l10n.sk.dph.reconciliation"]
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1)
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701"})
        # One § 43 intra-EU goods tax that feeds BOTH the súhrnný výkaz (kód 0)
        # and the priznanie r14 (base repartition tagged '14').
        tag14 = cls.env["account.account.tag"]._get_tax_tags(
            "14", cls.env.ref("base.sk").id)
        cls.tax43 = cls.env["account.tax"].create({
            "name": "§43 intra-EU goods 0%", "amount": 0.0,
            "amount_type": "percent", "type_tax_use": "sale",
            "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
            "tax_group_id": cls.tax_sale_a.tax_group_id.id,
            "cssk_ec_summary_code": "0",
            "invoice_repartition_line_ids": [
                Command.create({"repartition_type": "base",
                                "tag_ids": [Command.set(tag14.ids)]}),
                Command.create({"repartition_type": "tax"})],
            "refund_repartition_line_ids": [
                Command.create({"repartition_type": "base",
                                "tag_ids": [Command.set(tag14.ids)]}),
                Command.create({"repartition_type": "tax"})],
        })

    def _acc(self, code, account_type="expense"):
        acc = self.env["account.account"].search(
            [("code", "=like", code + "%"), ("company_ids", "in", self.company.id)],
            limit=1)
        if not acc:
            acc = self.env["account.account"].create({
                "name": code, "code": code, "account_type": account_type,
                "company_ids": [Command.set([self.company.id])]})
        return acc

    def test_sv_dph(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_eu, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax43, post=True)
        sv_version = self.env.ref("l10n_sk_ec_sales.sdv_version_2025")
        sv = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id, "version_id": sv_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": sv_version.statement_type_ids[0].id})
        sv.action_compute_lines()
        dp_version = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        dp = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": dp_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": dp_version.statement_type_ids[0].id})
        dp.action_compute_lines()

        row = self.recon.reconcile_sv_dph(sv, dp)[0]
        self.assertEqual(row["status"], "ok")
        self.assertAlmostEqual(row["left"], 1000.0, places=2)   # SV kód 0
        self.assertAlmostEqual(row["right"], 1000.0, places=2)  # priznanie r14
        self.assertEqual(self.recon.check_kontroly_sv_dph(sv, dp), [])

        # Break the tie (r14 no longer equals the súhrnný výkaz) -> SVDP_RECON.
        r14 = dp.line_ids.filtered(lambda l: l.code == "r14")
        r14.write({"is_overridden": True, "manual_value": 1500.0})
        dp.action_compute_lines()
        self.assertIn("SVDP_RECON",
                      [v["code"] for v in self.recon.check_kontroly_sv_dph(sv, dp)])

    def test_dph_books(self):
        # Domestic sale 1000 @ 23 % and purchase 500 @ 23 %: the daň booked to
        # the VAT account (343, via the tax lines) must tie to the priznanie.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[500.0], taxes=self.tax_purchase_a, post=True)
        dp_version = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        dp = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": dp_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": dp_version.statement_type_ids[0].id})
        dp.action_compute_lines()

        rows = {r["block"]: r for r in self.recon.reconcile_dph_books(dp)}
        self.assertEqual(rows["out_vat"]["status"], "ok")
        self.assertEqual(rows["in_vat"]["status"], "ok")
        self.assertEqual(rows["trzby"]["status"], "info")  # advisory only
        self.assertAlmostEqual(rows["out_vat"]["left"],
                               1000.0 * self.tax_sale_a.amount / 100.0, places=2)
        self.assertAlmostEqual(rows["out_vat"]["left"], rows["out_vat"]["right"], 2)
        self.assertAlmostEqual(rows["in_vat"]["left"], rows["in_vat"]["right"], 2)
        self.assertEqual(self.recon.check_kontroly_dph_books(dp), [])

        # Break the output tie (priznanie no longer matches the booked daň).
        r17 = dp.line_ids.filtered(lambda l: l.code == "r17")
        r17.write({"is_overridden": True, "manual_value": 9999.0})
        dp.action_compute_lines()
        self.assertIn("DPBOOK_RECON",
                      [v["code"] for v in self.recon.check_kontroly_dph_books(dp)])

    def test_vzs_dppo(self):
        # P&L: revenue 602 = 5000, expense 501 = 3000 -> VH pred zdanením 2000.
        # Also post income tax 595 (dodatočné odvody) = 200 and prevod podielov
        # 596 = 100: both sit BELOW VH pred zdanením (VZS r57+/r60), so neither
        # the VZS r56 nor the corrected DPPO r100 (…,-595,-596) may include them.
        rev = self._acc("602", "income")
        exp, a595, a596 = self._acc("501"), self._acc("595"), self._acc("596")
        bank = self._acc("221", "asset_cash")
        self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2025-06-30", "line_ids": [
                Command.create({"account_id": rev.id, "credit": 5000.0}),
                Command.create({"account_id": exp.id, "debit": 3000.0}),
                Command.create({"account_id": a595.id, "debit": 200.0}),
                Command.create({"account_id": a596.id, "debit": 100.0}),
                Command.create({"account_id": bank.id, "debit": 1700.0})],
        }).action_post()
        dppo = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2025").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        dppo.action_compute_lines()
        uzpod = self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})

        row = self.recon.reconcile_vzs_dppo(uzpod, dppo)[0]
        self.assertAlmostEqual(row["left"], 2000.0, places=2)   # VZS pred zdanením
        self.assertAlmostEqual(row["right"], 2000.0, places=2)  # DPPO r100
        self.assertEqual(row["status"], "ok")
        self.assertEqual(self.recon.check_kontroly_vzs_dppo(uzpod, dppo), [])

        # Break the tie (manual r100 override) -> VZSDPPO_RECON (error).
        r100 = dppo.line_ids.filtered(lambda l: l.code == "r100")
        r100.write({"is_overridden": True, "manual_value": 9999.0})
        dppo.action_compute_lines()
        self.assertIn("VZSDPPO_RECON",
                      [v["code"] for v in self.recon.check_kontroly_vzs_dppo(uzpod, dppo)])
