# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import Command
from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkDppo(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_cssk_dic = "2020317068"
        cls.company.company_registry = "36000001"
        cls.version = cls.env.ref("l10n_sk_dppo.dppo_version_2025")
        cls.type_r = cls.env.ref("l10n_sk_dppo.dppo_type_R_2025")

    def _make(self):
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.type_r.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31",
        })
        ret.action_compute_lines()
        return ret

    def test_tax_spine(self):
        """The tax spine computes r100→daň: r310→r400→r500→r510, the § 15 rate
        (r550), r600=base×rate, r800, and the § 46b minimálna daň (r810)."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 40000.0)   # úhrn príjmov → 10 % rate, min tax 340
        setv("r301", 50000.0)   # adjusted base
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertEqual(v["r550"], 10.0)              # 40k ≤ 100k → 10 %
        self.assertAlmostEqual(v["r310"], 50000.0, 2)
        self.assertAlmostEqual(v["r400"], 50000.0, 2)
        self.assertAlmostEqual(v["r500"], 50000.0, 2)
        self.assertAlmostEqual(v["r510"], 50000.0, 2)
        self.assertAlmostEqual(v["r600"], 5000.0, 2)   # 50000 × 10 %
        self.assertAlmostEqual(v["r800"], 5000.0, 2)
        self.assertAlmostEqual(v["r810"], 340.0, 2)    # § 46b minimálna daň
        self.assertAlmostEqual(v["r820"], 0.0, 2)      # daň > min tax
        self.assertAlmostEqual(v["r1050"], 5000.0, 2)  # daň na úhradu

        # Small base → minimálna daň dominates.
        setv("r301", 1000.0)
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r600"], 100.0, 2)    # 1000 × 10 %
        self.assertAlmostEqual(v["r820"], 340.0, 2)    # min tax kicks in
        self.assertAlmostEqual(v["r1050"], 340.0, 2)

    def test_tax_spine_half_up_rounding(self):
        """Statutory arithmetic rounds HALF-UP, not Python banker's rounding:
        r510 = 26.75 at the 10 % rate gives 2.675, which must round to r600 =
        2.68 (Python round(26.75 × 10 / 100, 2) yields 2.67)."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 40000.0)   # úhrn príjmov ≤ 100k → 10 % rate
        setv("r301", 26.75)
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertEqual(v["r550"], 10.0)
        self.assertAlmostEqual(v["r510"], 26.75, 2)
        # 26.75 × 10 % = 2.675 → HALF-UP 2.68 (banker's rounding gives 2.67)
        self.assertAlmostEqual(v["r600"], 2.68, 2)

    def test_dan_na_uhradu_cascade(self):
        """The r830/r900/r1050/r1080 tail, in both regimes.

        Normal tax dominates (r800 > r810): r820/r830 = 0, r900 stays 0, and
        r1050 = daň. Min tax dominates (r810 > r800): r820 = r810, r830 =
        r810 − r800 (§ 46b ods. 5 carry-forwardable surplus), r900 = r810,
        r1050 = minimálna daň. With no r1060/r1070/r1071, r1080 = r1050."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        # --- Regime 1: normal tax dominates (r800 = 5000 > r810 = 340) -------
        setv("r560", 40000.0)   # → 10 % rate, § 46b min tax 340
        setv("r301", 50000.0)   # base → r600 = r800 = 5000
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r800"], 5000.0, 2)
        self.assertAlmostEqual(v["r810"], 340.0, 2)
        self.assertAlmostEqual(v["r820"], 0.0, 2)     # daň > min tax
        self.assertAlmostEqual(v["r830"], 0.0, 2)     # no min-tax surplus
        self.assertAlmostEqual(v["r900"], 0.0, 2)     # not set when r810≤r800
        self.assertAlmostEqual(v["r1050"], 5000.0, 2)
        self.assertAlmostEqual(v["r1080"], 5000.0, 2)  # = r1050 (no additions)

        # --- Regime 2: minimálna daň dominates (r810 = 340 > r800 = 100) -----
        setv("r301", 1000.0)    # base → r600 = r800 = 100
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r800"], 100.0, 2)
        self.assertAlmostEqual(v["r810"], 340.0, 2)
        self.assertAlmostEqual(v["r820"], 340.0, 2)   # min tax kicks in
        self.assertAlmostEqual(v["r830"], 240.0, 2)   # 340 − 100 surplus
        self.assertAlmostEqual(v["r900"], 340.0, 2)   # = min tax
        self.assertAlmostEqual(v["r1050"], 340.0, 2)
        self.assertAlmostEqual(v["r1080"], 340.0, 2)

    def test_dan_na_uhradu_settlement_threshold(self):
        """r1100/r1101 settlement = r1080 − preddavky (r1040).

        A tax-to-pay (nedoplatok) ≤ 5 € is waived (§ 46 ods. 1) → r1100 = 0;
        just over the threshold it is paid in full. The waiver is asymmetric
        by law: an overpayment (preplatok, negative settle) is reported on
        r1101 with NO 5 € floor — that floor is applied by the tax office at
        refund time, not on the form line.

        NOTE (open sign convention — flagged for review): r1101 currently
        stores the preplatok as a NEGATIVE number. If the DPPOv25 eForm
        expects it as a positive magnitude, change the model and flip the
        expected value on the marked assertion below (the XSD does not
        constrain the sign, so only this test guards it)."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 0.0)       # no min tax → r800 dominates
        setv("r301", 100.0)     # → r600 = r800 = 10 → r1050 = r1080 = 10
        ret.action_compute_lines()
        self.assertAlmostEqual(
            ret.line_ids.filtered(lambda l: l.code == "r1080").value, 10.0, 2)

        def settle(preddavky):
            setv("r1040", preddavky)
            ret.action_compute_lines()
            v = {l.code: l.value for l in ret.line_ids}
            return v["r1100"], v["r1101"]

        # nedoplatok exactly 5.00 € → waived
        self.assertEqual(settle(5.0), (0.0, 0.0))
        # nedoplatok 5.01 € → paid in full (no de-minimis deduction)
        r1100, r1101 = settle(4.99)
        self.assertAlmostEqual(r1100, 5.01, 2)
        self.assertAlmostEqual(r1101, 0.0, 2)
        # preplatok 5.00 € → recorded despite equal magnitude (asymmetry)
        r1100, r1101 = settle(15.0)
        self.assertAlmostEqual(r1100, 0.0, 2)
        self.assertAlmostEqual(r1101, -5.0, 2)   # <-- sign convention (see NOTE)

    def test_r1080_total_tax_components(self):
        """r1080 = r1050 + r1060 + r1070 + r1071 (all added).

        NOTE (flagged for review): r1061 and r1062 exist as form lines but are
        deliberately NOT in this sum — confirm against the DPPOv25 poučenie
        that they do not belong in r1080."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 40000.0)
        setv("r301", 50000.0)   # → r1050 = 5000
        setv("r1060", 10.0)
        setv("r1070", 5.0)
        setv("r1071", 3.0)
        setv("r1061", 100.0)    # must be ignored by r1080
        setv("r1062", 100.0)    # must be ignored by r1080
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r1050"], 5000.0, 2)
        self.assertAlmostEqual(v["r1080"], 5018.0, 2)  # 5000 + 10 + 5 + 3

    def test_r900_zero_when_normal_tax(self):
        """r900 (suma na účely určenia výšky preddavkov) stays 0 when normal
        tax dominates (r810 ≤ r800) — the spine only sets r900 = r810 when the
        payer actually pays the minimálna daň.

        NOTE (open domain decision — flagged for review): this asserts the
        CURRENT behaviour (r900 = 0 in the normal-tax case). If r900 should
        instead derive from r800 for advance-payment purposes, change the
        model and update this expected value — the test exists to make that
        decision explicit rather than silent."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 40000.0)   # § 46b min tax = 340
        setv("r301", 50000.0)   # → r800 = 5000 ≫ 340, so normal tax dominates
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r800"], 5000.0, 2)
        self.assertAlmostEqual(v["r810"], 340.0, 2)
        self.assertGreater(v["r800"], v["r810"])  # regime precondition
        self.assertAlmostEqual(v["r900"], 0.0, 2)  # <-- see NOTE

        # Recompute after the min-tax regime had set r900: the base evaluator
        # unlinks+rebuilds every line, so r900 must return to 0 (guards the
        # "stale value" false-positive from the second-opinion review).
        setv("r301", 1000.0)                       # r800 = 100 < 340 → r900 = 340
        ret.action_compute_lines()
        self.assertAlmostEqual(
            ret.line_ids.filtered(lambda l: l.code == "r900").value, 340.0, 2)
        setv("r301", 50000.0)                      # back to normal-tax regime
        ret.action_compute_lines()
        self.assertAlmostEqual(
            ret.line_ids.filtered(lambda l: l.code == "r900").value, 0.0, 2)

    def test_dodatocne_differences(self):
        """Dodatočné DPPO auto-fills r1120 (posledná známa daň = previous r1050)
        and r1130 (rozdiel = this − previous); loss rows stay 0 (tax→tax)."""
        orig = self._make()
        orig.line_ids.filtered(lambda l: l.code == "r1050").write(
            {"is_overridden": True, "manual_value": 420.0})
        orig.action_compute_lines()
        orig.action_export_xml()
        orig.action_submit()

        amend = self.env["cssk.income.tax.return"].browse(
            orig.action_create_amendment()["res_id"])
        amend.statement_type_id = self.env.ref("l10n_sk_dppo.dppo_type_D_2025").id
        self.assertEqual(amend.original_return_id, orig)
        # corrected (higher) tax
        amend.line_ids.filtered(lambda l: l.code == "r1050").write(
            {"is_overridden": True, "manual_value": 500.0})
        amend.action_compute_lines()

        vals = {l.code: l.value for l in amend.line_ids}
        self.assertAlmostEqual(vals["r1120"], 420.0, places=2)  # posledná známa daň
        self.assertAlmostEqual(vals["r1130"], 80.0, places=2)   # rozdiel 500 − 420
        self.assertAlmostEqual(vals["r1140"], 0.0, places=2)    # žiadna strata
        self.assertAlmostEqual(vals["r1150"], 0.0, places=2)

    def test_export_validates_against_official_xsd(self):
        ret = self._make()
        # action_export_xml renders + asserts validity against dppo2025.xsd
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        self.assertTrue(ret.xml_attachment_id)

    def test_dppo_2024_export_validates_against_official_xsd(self):
        """The DPPOv24 export renders the computed spine into the official
        form.597 structure and validates against dppo2024.xsd (root <dokument>,
        r1050 carries the computed daň)."""
        import base64
        import os
        from lxml import etree
        v24 = self.env.ref("l10n_sk_dppo.dppo_version_2024")
        # wire template + official XSD (the version record is noupdate, so a
        # pre-existing test DB may not have them on the record yet)
        xsd = os.path.join(os.path.dirname(__file__), "..", "data", "dppo2024.xsd")
        with open(xsd, "rb") as fh:
            v24.write({"xml_template_ref_id":
                       self.env.ref("l10n_sk_dppo.dppo2024_xml").id,
                       "xml_schema_filename": "dppo2024.xsd",
                       "xml_schema_data": base64.b64encode(fh.read())})
        self.company.write({"city": "Bratislava", "zip": "81101",
                            "street": "Test 1"})
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": v24.id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2024").id,
            "date_from": "2024-01-01", "date_to": "2024-12-31"})
        ret.action_compute_lines()
        for code, val in (("r100", 19790.86), ("r110", 927.14),
                          ("r410", 10359.00), ("r560", 116161.85)):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})
        ret.action_compute_lines()
        ret.action_export_xml()                # validates vs dppo2024.xsd
        self.assertEqual(ret.state, "exported")
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext(".//r1050"), "2175.39")   # daň renders
        self.assertEqual(root.findtext(".//r301"), "20718.00")   # base renders
        self.assertIsNone(root.find(".//r503"))                  # 2025-only, absent

    def test_r100_from_profit_and_loss(self):
        # Post a simple P&L: revenue 6xx 5000, expense 5xx 3000 -> profit 2000.
        Account = self.env["account.account"]
        income = Account.search(
            [("code", "=like", "602%"), ("company_ids", "in", self.company.id)],
            limit=1,
        )
        expense = Account.search(
            [("code", "=like", "501%"), ("company_ids", "in", self.company.id)],
            limit=1,
        )
        bank = Account.search(
            [("code", "=like", "221%"), ("company_ids", "in", self.company.id)],
            limit=1,
        )
        self.assertTrue(income and expense and bank, "SK chart accounts present")
        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": income.id, "credit": 5000.0}),
                Command.create({"account_id": expense.id, "debit": 3000.0}),
                Command.create({"account_id": bank.id, "debit": 2000.0}),
            ],
        })
        move.action_post()
        ret = self._make()
        r100 = ret.line_ids.filtered(lambda l: l.code == "r100").value
        self.assertAlmostEqual(r100, 2000.0, places=2)

    def test_post_income_tax_provision(self):
        """The provision action books the computed tax MD 591 / D 341 at period
        end, links the entry, guards double-posting, and reverses cleanly."""
        self.version.provision_line_code = "r1050"

        def acc(code, atype):
            a = self.env["account.account"].search(
                [("code", "=like", code + "%"),
                 ("company_ids", "in", self.company.id)], limit=1)
            if not a:
                a = self.env["account.account"].create({
                    "name": code, "code": code + "000", "account_type": atype,
                    "company_ids": [Command.set([self.company.id])]})
            return a
        exp, pay = acc("591", "expense"), acc("341", "liability_current")

        ret = self._make()
        for code, val in (("r560", 40000.0), ("r301", 50000.0)):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})
        ret.action_compute_lines()
        self.assertAlmostEqual(ret.provision_amount, 5000.0, 2)   # r1050

        ret.action_post_provision()
        move = ret.provision_move_id
        self.assertTrue(move and move.state == "posted")
        self.assertEqual(move.date.isoformat(), "2025-12-31")     # period end
        deb = move.line_ids.filtered(lambda l: l.debit > 0)
        cred = move.line_ids.filtered(lambda l: l.credit > 0)
        self.assertEqual(deb.account_id, exp)                     # MD 591
        self.assertEqual(cred.account_id, pay)                    # D 341
        self.assertAlmostEqual(deb.debit, 5000.0, 2)
        self.assertAlmostEqual(cred.credit, 5000.0, 2)
        self.assertTrue(ret.provision_posted)

        # double-post is blocked
        with self.assertRaises(UserError):
            ret.action_post_provision()

        # reverse clears the link (and books a cancelling reversal)
        ret.action_reverse_provision()
        self.assertFalse(ret.provision_move_id)
        self.assertFalse(ret.provision_posted)

    def test_rate_bands_come_from_version_data(self):
        """§ 15 rates are version DATA (rate_bands on the version record),
        not code: inclusive upper bounds, null-bounded top band."""
        ret = self._make()
        self.assertEqual(
            self.version.rate_bands,
            [[100000.0, 10.0], [5000000.0, 21.0], [None, 24.0]])
        self.assertEqual(ret._dppo_rate(0.0), 10.0)
        self.assertEqual(ret._dppo_rate(100000.0), 10.0)   # bound inclusive
        self.assertEqual(ret._dppo_rate(100000.01), 21.0)
        self.assertEqual(ret._dppo_rate(5000000.0), 21.0)  # bound inclusive
        self.assertEqual(ret._dppo_rate(5000000.01), 24.0)

        ret24 = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2024").id,
            "statement_type_id": self.env.ref(
                "l10n_sk_dppo.dppo_type_R_2024").id,
            "date_from": "2024-01-01", "date_to": "2024-12-31"})
        self.assertEqual(ret24._dppo_rate(60000.0), 15.0)  # bound inclusive
        self.assertEqual(ret24._dppo_rate(60000.01), 21.0)

    def test_min_tax_bands_come_from_version_data(self):
        """§ 46b minimum-tax amounts are version DATA (min_tax_bands):
        340/960/1920/3840 € by r560, inclusive bounds; r560 ≤ 0 → no min
        tax; short periods prorate by months (HALF-UP)."""
        ret = self._make()
        self.assertEqual(
            self.version.min_tax_bands,
            [[50000.0, 340.0], [250000.0, 960.0], [500000.0, 1920.0],
             [None, 3840.0]])
        self.assertEqual(ret._dppo_min_tax(0.0), 0.0)
        self.assertEqual(ret._dppo_min_tax(-5.0), 0.0)
        self.assertEqual(ret._dppo_min_tax(1.0), 340.0)
        self.assertEqual(ret._dppo_min_tax(50000.0), 340.0)
        self.assertEqual(ret._dppo_min_tax(50000.01), 960.0)
        self.assertEqual(ret._dppo_min_tax(250000.0), 960.0)
        self.assertEqual(ret._dppo_min_tax(250000.01), 1920.0)
        self.assertEqual(ret._dppo_min_tax(500000.0), 1920.0)
        self.assertEqual(ret._dppo_min_tax(500000.01), 3840.0)
        # month proration: 5-month period → 340 / 12 × 5 = 141.67 (HALF-UP)
        ret.write({"date_from": "2025-08-01", "date_to": "2025-12-31"})
        self.assertAlmostEqual(ret._dppo_min_tax(1000.0), 141.67, places=2)

    def test_version_without_bands_raises_loudly(self):
        """A version lacking (or with malformed) bands must raise a UserError
        instead of silently applying a wrong statutory rate."""
        ret = self._make()
        self.version.rate_bands = False
        with self.assertRaises(UserError):
            ret._dppo_rate(1000.0)
        with self.assertRaises(UserError):
            ret.action_compute_lines()   # the spine calls _dppo_rate
        # malformed: no null-bounded catch-all top band
        self.version.rate_bands = [[100000.0, 10.0]]
        with self.assertRaises(UserError):
            ret._dppo_rate(1000.0)
        # min-tax bands are guarded the same way
        self.version.rate_bands = [[None, 21.0]]
        self.version.min_tax_bands = False
        with self.assertRaises(UserError):
            ret._dppo_min_tax(1000.0)

    def test_dppo_2024_version_rate(self):
        """The SK DPPO 2024 version applies the 2024 § 15 schedule (15 % ≤ 60k €
        else 21 %), not 2025's 10/21/24 %. Confirms the year-aware rate via the
        proper 2024 version — the import's r550 = 15 % was just r560 = 0."""
        v2024 = self.env.ref("l10n_sk_dppo.dppo_version_2024")
        self.assertEqual(v2024.valid_from.isoformat(), "2024-01-01")
        self.assertEqual(v2024.valid_to.isoformat(), "2024-12-31")
        self.assertEqual(v2024.provision_line_code, "r1050")

        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": v2024.id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2024").id,
            "date_from": "2024-01-01", "date_to": "2024-12-31"})

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        ret.action_compute_lines()
        setv("r301", 10000.0)                 # tax base (after adjustments)

        # úhrn príjmov > 60 000 € → 21 % (the FY2024 real case)
        setv("r560", 116161.85)
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertEqual(v["r550"], 21.0)
        self.assertAlmostEqual(v["r600"], 2100.0, 2)    # 10000 × 21 %

        # úhrn príjmov ≤ 60 000 € → 15 %
        setv("r560", 40000.0)
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertEqual(v["r550"], 15.0)
        self.assertAlmostEqual(v["r600"], 1500.0, 2)    # 10000 × 15 %

    def test_base_cascade_reproduces_mrp_2024(self):
        """The base flows from r100: r200 = Σ add-backs, r300 = Σ deductions,
        r301 = r100 + r200 − r300. Reproduces the FY2024 real case to the cent —
        the import's 960 came from entering r301 as the add-backs (927) instead
        of the base (20 718); the user now enters only the judgment rows."""
        v2024 = self.env.ref("l10n_sk_dppo.dppo_version_2024")
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": v2024.id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2024").id,
            "date_from": "2024-01-01", "date_to": "2024-12-31"})
        ret.action_compute_lines()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r100", 19790.86)     # účtovný výsledok pred zdanením (GL)
        setv("r110", 927.14)       # pripočítateľné (PHM/reprez./pokuty/…)
        setv("r410", 10359.00)     # odpočet daňovej straty 2023 (50 % cap)
        setv("r560", 116161.85)    # úhrn zdaniteľných príjmov → 21 %
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r200"], 927.14, 2)     # add-backs súčet
        self.assertAlmostEqual(v["r301"], 20718.00, 2)   # base = r100 + 927.14
        self.assertAlmostEqual(v["r510"], 10359.00, 2)   # − loss 10 359
        self.assertEqual(v["r550"], 21.0)                # > 60k € → 21 %
        self.assertAlmostEqual(v["r600"], 2175.39, 2)
        self.assertAlmostEqual(v["r1050"], 2175.39, 2)   # = MRP, to the cent
