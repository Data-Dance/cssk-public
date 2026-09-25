# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkDphReconciliation(AccountTestInvoicingCommon):
    """KV DPH ↔ DPH priznanie cross-form reconciliation, both built from the
    same posted SK data."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })
        cls.partner_a.country_id = cls.env.ref("base.sk")
        cls.partner_a.vat = "SK2023456787"
        cls.tax_sale = cls.tax_sale_a
        cls.tax_purchase = cls.tax_purchase_a

        cls.kv_version = cls.env.ref("l10n_sk_kv_dph.kvdph_version_2025v1")
        cls.dp_version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")
        cls.recon = cls.env["l10n.sk.dph.reconciliation"]

    def _make_kv(self):
        return self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.kv_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.kv_version.statement_type_ids[0].id,
        })

    def _make_dp(self):
        return self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.dp_version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.dp_version.statement_type_ids[0].id,
        })

    def _status(self, rows, block):
        return next(r for r in rows if r["block"] == block)

    def test_reconcile_matches_then_flags_overstatement(self):
        # One domestic sale to a platiteľ (→ KV A.1 + DP output) and one
        # domestic purchase with deduction (→ KV B.2 + DP odpočet). Both the
        # KV and the priznanie see the same daň, so the blocks reconcile.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-12",
            amounts=[500.0], taxes=self.tax_purchase, post=True)

        kv = self._make_kv()
        kv.action_compute_lines()
        dp = self._make_dp()
        dp.action_compute_lines()

        rows = self.recon.reconcile(kv, dp)
        # Output (A.1 daň == DP r04) and deduction (B.2 daň == DP odpočet) tie
        # out exactly; no self-assessment in this data set.
        self.assertEqual(self._status(rows, "output")["status"], "ok",
                         "A.1 daň must reconcile with the priznanie output rows")
        self.assertEqual(self._status(rows, "deduction")["status"], "ok",
                         "B.2 odpočet must reconcile with the priznanie odpočet")
        self.assertEqual(self.recon.check_kontroly(kv, dp), [],
                         "a consistent KV/DP pair has no reconciliation warnings")

        # Overstate the KV output (A.1 daň now exceeds the priznanie) -> the
        # reconciliation must flag it (KV ⊆ DP is violated).
        kv.sk_section_a1_ids[0].tax_amount += 999.0
        rows = self.recon.reconcile(kv, dp)
        self.assertEqual(self._status(rows, "output")["status"], "over")
        codes = [v["code"] for v in self.recon.check_kontroly(kv, dp)]
        self.assertIn("KVDP_RECON", codes,
                      "KV daň exceeding the priznanie must raise KVDP_RECON")
