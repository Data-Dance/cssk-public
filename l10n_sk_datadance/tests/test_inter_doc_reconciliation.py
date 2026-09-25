# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkInterDocRecon(AccountTestInvoicingCommon):
    """SV ↔ DPH priznanie and priznanie ↔ účtovníctvo cross-form
    reconciliations, all built from the same posted SK data.

    The VZS → DPPO reconciliation is tested in ``l10n_sk_dppo_fs``, the bridge
    that owns it."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava",
                           "country_id": cls.env.ref("base.sk").id})
        cls.recon = cls.env["l10n.sk.dph.reconciliation"]
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

    def test_the_books_reconciliation_lands_on_the_screen_not_the_chatter(self):
        """The button Radovan actually presses, and what it must produce.

        It posted a ``<ul>`` to the chatter and returned a toast reading
        "pozri záznam", which is both unreadable at 217 filings and a log
        rather than a worklist. Every row now becomes a comparison record:
        the two that are controls, and the tržby row that is informational and
        must NOT read as a difference — an accountant sent to chase the gap
        between the VAT base and účtová trieda 60 is being sent after a number
        that is doing exactly what it should.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        dp_version = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        dp = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": dp_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": dp_version.statement_type_ids[0].id})
        dp.action_compute_lines()

        before = dp.message_ids
        result = dp.action_reconcile_books()
        self.assertFalse(dp.message_ids - before,
                         "reconciling must not post to the chatter")
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "cssk.filing.discrepancy")

        rows = {r.code: r for r in self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", dp.id),
            ("basis", "=", "ledger")])}
        self.assertEqual(set(rows), {"out_vat", "in_vat", "trzby"})
        self.assertEqual(rows["out_vat"].kind, "ok")
        self.assertEqual(rows["trzby"].kind, "info",
                         "the tržby tie is advisory and must not read as a "
                         "difference")
        self.assertEqual(rows["trzby"].state, "agrees",
                         "and must stay out of the worklist")
        self.assertTrue(rows["out_vat"].row_label,
                        "every reconciliation row carries its name")
