# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkExemptRows(AccountTestInvoicingCommon):
    """r13 / r14 as the poučenie defines them (DPHv25 bod 31, and r15 / r16 in
    the vzory to 2020).

    r14 is § 43 ods. 1 a 4 GOODS only. A § 15 service to another member state
    is not exempt and is on no row; the first buyer of a trojstranný obchod is
    excluded from r13 and r14 in so many words. r13 is every exempt supply,
    goods to the EU and exports included."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cid = cls.company.id
        ref = lambda x: cls.env.ref("account.%s_%s" % (cid, x))  # noqa: E731
        cls.eu_goods = ref("vy_eu_m")
        cls.eu_service = ref("vy_eu_s")
        cls.eu_triangular = ref("vy_eu_t")
        cls.export = ref("vy_mimo_eu")
        cls.domestic_exempt = ref("vy_tuz_0")
        cls.customer = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701"})
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")

    def _values(self, *sales):
        for amount, tax in sales:
            self.init_invoice(
                "out_invoice", partner=self.customer, invoice_date="2026-06-10",
                amounts=[amount], taxes=tax, post=True)
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        return ret, {line.code: line.value for line in ret.line_ids}

    def _r14_tagged(self, tax):
        tags = self.env["account.account.tag"]._get_tax_tags(
            "14", self.env.ref("base.sk").id)
        return bool((tax.invoice_repartition_line_ids
                     | tax.refund_repartition_line_ids).tag_ids & tags)

    def test_a_company_charted_now_has_no_r14_on_services_or_triangular(self):
        # setUpClass charted this company after the install: the chart hook,
        # not the install hook, is what took the tag off.
        self.assertFalse(self._r14_tagged(self.eu_service))
        self.assertFalse(self._r14_tagged(self.eu_triangular))
        self.assertTrue(self._r14_tagged(self.eu_goods),
                        "§ 43 goods are what r14 is for")

    def test_an_eu_service_is_on_no_row_and_goods_are_on_r13_and_r14(self):
        _ret, vals = self._values((1000.0, self.eu_service),
                                  (300.0, self.eu_goods))
        self.assertAlmostEqual(vals["r14"], 300.0, places=2)
        self.assertAlmostEqual(vals["r13"], 300.0, places=2)

    def test_the_first_buyer_s_triangular_supply_is_on_neither(self):
        _ret, vals = self._values((500.0, self.eu_triangular))
        self.assertAlmostEqual(vals["r13"], 0.0, places=2)
        self.assertAlmostEqual(vals["r14"], 0.0, places=2)

    def test_r13_totals_every_exempt_supply(self):
        _ret, vals = self._values((100.0, self.domestic_exempt),
                                  (200.0, self.eu_goods),
                                  (400.0, self.export))
        self.assertAlmostEqual(vals["r14"], 200.0, places=2)
        self.assertAlmostEqual(vals["r15"], 400.0, places=2)
        self.assertAlmostEqual(vals["r13"], 700.0, places=2)

    def test_r13_drills_into_what_it_totals(self):
        ret, _vals = self._values((100.0, self.domestic_exempt),
                                  (200.0, self.eu_goods))
        r13 = ret.line_ids.filtered(lambda l: l.code == "r13")
        self.assertTrue(r13.source_reconciles)

    def test_no_tax_carries_two_of_the_rows_r13_adds_up(self):
        # r13 sums tags 13, 14 and 15 term by term; a line carrying two of
        # them would be counted twice.
        sk = self.env.ref("base.sk").id
        Tag = self.env["account.account.tag"]
        rows = [Tag._get_tax_tags(code, sk) for code in ("13", "14", "15")]
        taxes = self.env["account.tax"].search(
            [("company_id", "=", self.company.id)])
        reps = (taxes.invoice_repartition_line_ids
                | taxes.refund_repartition_line_ids)
        for rep in reps:
            self.assertLessEqual(
                sum(1 for tags in rows if rep.tag_ids & tags), 1,
                rep.tax_id.name)

    def test_an_already_posted_service_line_is_retagged(self):
        """The upgrade retags lines posted before it, from the taxes'
        current repartition — and leaves the goods line alone."""
        tags = self.env["account.account.tag"]._get_tax_tags(
            "14", self.env.ref("base.sk").id)
        service = self.init_invoice(
            "out_invoice", partner=self.customer, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.eu_service, post=True)
        goods = self.init_invoice(
            "out_invoice", partner=self.customer, invoice_date="2026-06-10",
            amounts=[300.0], taxes=self.eu_goods, post=True)
        service_line = service.invoice_line_ids
        # As it was posted before the fix: SQL, the way the old chart left it.
        self.env.flush_all()
        self.env.cr.execute(
            "INSERT INTO account_account_tag_account_move_line_rel "
            "(account_move_line_id, account_account_tag_id) VALUES (%s, %s)",
            (service_line.id, tags[:1].id))
        service_line.invalidate_recordset(["tax_tag_ids"])
        self.assertTrue(service_line.tax_tag_ids & tags)

        retagged = self.env["account.chart.template"]._cssk_sk_drop_r14_tag(
            self.company)
        self.assertEqual(retagged, 1)
        self.assertFalse(service_line.tax_tag_ids & tags)
        self.assertTrue(goods.invoice_line_ids.tax_tag_ids & tags)
        self.assertEqual(
            self.env["account.chart.template"]._cssk_sk_drop_r14_tag(
                self.company), 0, "re-running changes nothing")


@tagged("post_install", "-at_install")
class TestSkDebitNotes(AccountTestInvoicingCommon):
    """A received ťarchopis corrects the deduction on r28 (§ 53, poučenie
    bod 43), minus when it rises — not a new deduction on r19 – r21."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cid = cls.company.id
        cls.domestic = cls.env.ref("account.%s_vs_tuz_23" % cid)
        cls.reverse_charge = cls.env.ref("account.%s_vs_rc_23" % cid)
        cls.supplier = cls.env["res.partner"].create({
            "name": "Dodávateľ s.r.o.", "country_id": cls.env.ref("base.sk").id})
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")
        Move = cls.env["account.move"]
        cls.has_origin = "debit_origin_id" in Move._fields
        cls.has_declared = "cssk_vat_correction" in Move._fields

    def _bill(self, tax, date, amount=100.0, **vals):
        bill = self.init_invoice(
            "in_invoice", partner=self.supplier, invoice_date=date,
            amounts=[amount], taxes=tax)
        if vals:
            bill.write(vals)
        bill.action_post()
        return bill

    def _june(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        return ret, {line.code: line.value for line in ret.line_ids}

    def _debit_note(self, tax):
        if self.has_origin:
            # The supplier's numbers: with l10n_sk_kv_dph installed a
            # received debit note does not post without them.
            original = self._bill(tax, "2026-05-10", ref="DF-2026-0001")
            return self._bill(tax, "2026-06-10", debit_origin_id=original.id,
                              ref="TAR-2026-0001")
        self.assertTrue(self.has_declared,
                        "neither account_debit_note nor l10n_cssk_kv_kh_base "
                        "is installed: nothing can mark a debit note")
        return self._bill(tax, "2026-06-10", cssk_vat_correction="yes",
                          ref="TAR-2026-0001",
                          cssk_control_original_ref="DF-2026-0001")

    def test_an_ordinary_bill_still_deducts_on_r21(self):
        self._bill(self.domestic, "2026-06-10")
        _ret, vals = self._june()
        self.assertAlmostEqual(vals["r21"], 23.0, places=2)
        self.assertAlmostEqual(vals["r28"], 0.0, places=2)

    def test_a_domestic_debit_note_corrects_on_r28_with_a_minus(self):
        self._debit_note(self.domestic)
        ret, vals = self._june()
        self.assertAlmostEqual(vals["r21"], 0.0, places=2)
        self.assertAlmostEqual(vals["r19_total"], 0.0, places=2)
        self.assertAlmostEqual(vals["r28"], -23.0, places=2)
        # The same money as a deduction: an excess of 23 either way.
        self.assertAlmostEqual(vals["r33"], 23.0, places=2)
        for code in ("r21", "r28"):
            line = ret.line_ids.filtered(lambda l, c=code: l.code == c)
            self.assertTrue(line.source_reconciles, code)

    def test_a_self_assessed_debit_note_corrects_r24_r25_and_r28(self):
        self._debit_note(self.reverse_charge)
        ret, vals = self._june()
        for code in ("r09b", "r10b", "r19"):
            self.assertAlmostEqual(vals[code], 0.0, places=2, msg=code)
        # Base and tax raised (plus), deduction raised (minus): bod 39/40/43.
        self.assertAlmostEqual(vals["r24"], 100.0, places=2)
        self.assertAlmostEqual(vals["r25"], 23.0, places=2)
        self.assertAlmostEqual(vals["r28"], -23.0, places=2)
        self.assertAlmostEqual(vals["r32"], 0.0, places=2)
        self.assertAlmostEqual(vals["r33"], 0.0, places=2)
        for code in ("r24", "r25", "r28"):
            line = ret.line_ids.filtered(lambda l, c=code: l.code == c)
            self.assertTrue(line.source_reconciles, code)

    def test_a_declared_correction_without_an_origin_is_a_debit_note(self):
        """An imported ťarchopis whose original lives in another agenda."""
        if not self.has_declared:
            self.skipTest("l10n_cssk_kv_kh_base is not installed")
        self._bill(self.domestic, "2026-06-10", cssk_vat_correction="yes",
                   ref="TAR-2026-0002", cssk_control_original_ref="DF-2026-0002")
        _ret, vals = self._june()
        self.assertAlmostEqual(vals["r21"], 0.0, places=2)
        self.assertAlmostEqual(vals["r28"], -23.0, places=2)

    def test_declaring_no_overrides_the_origin(self):
        if not (self.has_declared and self.has_origin):
            self.skipTest("needs account_debit_note and l10n_cssk_kv_kh_base")
        original = self._bill(self.domestic, "2026-05-10")
        self._bill(self.domestic, "2026-06-10", debit_origin_id=original.id,
                   cssk_vat_correction="no")
        _ret, vals = self._june()
        self.assertAlmostEqual(vals["r21"], 23.0, places=2)
        self.assertAlmostEqual(vals["r28"], 0.0, places=2)
