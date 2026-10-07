# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkDppo(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"
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


@tagged("post_install", "-at_install")
class TestLicenciaBlock(AccountTestInvoicingCommon):
    """§ 46b: the bands, and which row carries the kladný rozdiel.

    Both were wrong in ways nothing on the reference agenda could show. Its
    two filed DPPO years are losses, so the computed daň is 0,00 and the
    licencia, the daň na úhradu and the kladný rozdiel all collapse onto one
    number — a fixture whose inputs collapse several quantities cannot tell
    them apart, however exactly it reconciles.

    So these test the shape against Finančná správa's own worked example
    (usmernenie 20. 12. 2018) rather than against any agenda.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"
        cls.company.company_registry = "36000001"
        cls.company.vat = "SK2020317068"
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

    def _version(self, year):
        return self.env.ref("l10n_sk_dppo.dppo_version_%s" % year)

    # ------------------------------------------------------------------
    # which row carries the kladný rozdiel
    # ------------------------------------------------------------------
    def test_the_licencia_vzory_have_no_r830_to_put_it_on(self):
        """The fact the routing turns on, asserted from the shipped data.

        The FS schemas give 2017/2018/2019 as r800/r810/r820 with no r830,
        while 2013-2015 and 2024+ define r830 as well. If a future vintage
        breaks that, the spine's branch silently changes meaning.
        """
        for year in ("2017", "2018", "2019"):
            codes = set(self._version(year).line_def_ids.mapped("code"))
            self.assertIn("r820", codes, "%s must define r820" % year)
            self.assertNotIn(
                "r830", codes,
                "%s defines r830 — the kladný rozdiel would move rows" % year)
        for year in ("2013", "2014", "2015", "2024"):
            codes = set(self._version(year).line_def_ids.mapped("code"))
            self.assertIn(
                "r830", codes, "%s is expected to define r830" % year)

    def test_the_worked_example_from_the_usmernenie(self):
        """FS SR's own example, driven through the real spine.

        Usmernenie 20. 12. 2018, licencia-era vzor::

            r. 800 – Daň po úľavách a po zápočte dane      600
            r. 810 – Daňová licencia                       960
            r. 820 – Kladný rozdiel medzi licenciou a daňou 360
            r. 900 – Daňová licencia na úhradu             960

        r820 is 360, not 960. The spine used to write r810 there on every
        vintage — correct for the minimálna daň forms, wrong for these three.
        """
        version = self.env.ref("l10n_sk_dppo.dppo_version_2017")
        # The 2017 vzor has NO r560, so the band is keyed on class 6 revenue.
        # 100 000 keeps us under the 500 000 bound; the company carries a VAT
        # number, so the platiteľ band applies: 960.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2017-06-30",
            amounts=[100000.0], taxes=self.env["account.tax"], post=True,
        )
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": version.id,
            "statement_type_id": self.env.ref(
                "l10n_sk_dppo.dppo_type_R_2017").id,
            "date_from": "2017-01-01", "date_to": "2017-12-31",
        })
        ret.action_compute_lines()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        # 21 % of 2 857,14 = 600,00 exactly once rounded — the example's daň.
        setv("r301", 2857.14)
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}

        self.assertAlmostEqual(v["r800"], 600.0, places=2,
                               msg="fixture: daň po úľavách must be 600,00")
        self.assertAlmostEqual(v["r810"], 960.0, places=2,
                               msg="platiteľ DPH, obrat ≤ 500 000 → 960")
        self.assertAlmostEqual(
            v["r820"], 360.0, places=2,
            msg="the licencia vzor files the KLADNÝ ROZDIEL on r820, not the "
                "licencia itself")
        self.assertNotIn("r830", v, "the 2017 vzor has no r830")

    def test_the_min_tax_vzory_keep_the_other_shape(self):
        """2024+ has r830, so the rozdiel goes there and r820 keeps its own
        meaning. Guards the branch from being 'simplified' into one rule."""
        ret = self._make()

        def setv(code, val):
            ret.line_ids.filtered(lambda l: l.code == code).write(
                {"is_overridden": True, "manual_value": val})

        setv("r560", 40000.0)   # § 46b minimálna daň 340
        setv("r301", 1000.0)    # → r800 = 100
        ret.action_compute_lines()
        v = {l.code: l.value for l in ret.line_ids}
        self.assertAlmostEqual(v["r800"], 100.0, places=2)
        self.assertAlmostEqual(v["r810"], 340.0, places=2)
        self.assertAlmostEqual(v["r820"], 340.0, places=2)
        self.assertAlmostEqual(v["r830"], 240.0, places=2)

    # ------------------------------------------------------------------
    # the bands
    # ------------------------------------------------------------------
    def test_the_licencia_bands_are_seeded_on_the_licencia_vintages(self):
        for year in ("2014", "2015", "2017", "2018", "2019"):
            bands = self._version(year).min_tax_bands
            self.assertTrue(
                bands, "%s carries no § 46b bands — r810 would compute 0 "
                       "while the taxpayer owed a licencia" % year)

    def test_480_and_960_sit_at_the_same_turnover_and_differ_by_vat_status(self):
        """The reason a band needs a condition at all.

        A one-dimensional table keyed on turnover cannot express § 46b ods. 2:
        both amounts apply at ≤ 500 000 € and only the platiteľ status
        separates them.
        """
        Return = self.env["cssk.income.tax.return"]
        bands = self._version("2017").min_tax_bands
        payer = {"vat_payer": True, "not_vat_payer": False}
        nonpayer = {"vat_payer": False, "not_vat_payer": True}

        self.assertAlmostEqual(
            Return._dppo_band_value(bands, 400000.0, payer), 960.0, places=2)
        self.assertAlmostEqual(
            Return._dppo_band_value(bands, 400000.0, nonpayer), 480.0, places=2)
        # Above the bound neither condition matters.
        for conds in (payer, nonpayer):
            self.assertAlmostEqual(
                Return._dppo_band_value(bands, 900000.0, conds), 2880.0,
                places=2)

    def test_an_unevaluable_condition_is_skipped_not_applied(self):
        """A band nobody can evaluate must not be chosen by accident."""
        Return = self.env["cssk.income.tax.return"]
        bands = [[1000.0, 111.0, "never_set"], [None, 222.0]]
        self.assertAlmostEqual(
            Return._dppo_band_value(bands, 500.0, {}), 222.0, places=2)

    def test_a_band_without_a_condition_still_works(self):
        """The 2024 minimálna daň table has no conditions and must not break."""
        Return = self.env["cssk.income.tax.return"]
        bands = self._version("2024").min_tax_bands
        self.assertTrue(bands)
        self.assertAlmostEqual(
            Return._dppo_band_value(bands, 100000.0, {}), 960.0, places=2)


class TestDerivedCodesHook(TransactionCase):
    """``_cssk_derived_codes`` must agree with what the spine actually writes.

    A comparator against a filed return needs three states, and ``kind`` only
    gives two: it names where a row's INPUT comes from, not whether this layer
    then overwrites the row. Nineteen DPPO rows are ``kind='manual'`` and
    derived — r310 and r400 among them — so a bridge filtering on ``kind``
    either compares rows it cannot check or skips rows it can.

    The set lived only inside ``_compute_tax_spine`` until now, which meant the
    only way for a second consumer to have it was to copy it. That is the
    duplicated-formula defect, so the declaration is single and ``put()``
    enforces it; this holds the hook to the declaration.
    """

    def _sk_versions(self):
        versions = self.env["cssk.income.tax.version"].search(
            [("country_id.code", "=", "SK")])
        self.assertTrue(versions, "no SK DPPO versions seeded")
        return versions

    def test_the_hook_returns_only_rows_the_vzor_defines(self):
        for version in self._sk_versions():
            codes = set(version.line_def_ids.mapped("code"))
            derived = version._cssk_derived_codes()
            self.assertTrue(
                derived, "%s derives nothing at all" % version.name)
            self.assertFalse(
                derived - codes,
                "%s: hook names rows the vzor has not got: %s"
                % (version.name, sorted(derived - codes)))

    def test_the_hook_matches_the_spine_declaration(self):
        from odoo.addons.l10n_sk_dppo.models.cssk_income_tax import _SPINE_ROWS
        for version in self._sk_versions():
            codes = set(version.line_def_ids.mapped("code"))
            self.assertEqual(
                version._cssk_derived_codes(), codes & set(_SPINE_ROWS),
                "%s: the hook and the spine's declaration disagree"
                % version.name)

    def test_derived_rows_are_not_distinguishable_by_kind(self):
        """The fact that makes the hook necessary, asserted so it stays true.

        If a future change ever gave the derived rows a kind of their own,
        this fails — and at that point the hook can be retired rather than
        left as a second way of asking the same question.
        """
        for version in self._sk_versions():
            derived = version._cssk_derived_codes()
            kinds = set(version.line_def_ids.filtered(
                lambda d: d.code in derived).mapped("kind"))
            self.assertEqual(
                kinds, {"manual"},
                "%s: derived rows now carry kinds %s — if `kind` can express "
                "'derived', _cssk_derived_codes is redundant"
                % (version.name, sorted(kinds)))

    def test_a_non_sk_version_derives_nothing(self):
        """The base's contract: only a country layer knows its own spine."""
        other = self.env["cssk.income.tax.version"].search(
            [("country_id.code", "!=", "SK")], limit=1)
        if not other:
            self.skipTest("no non-SK income-tax version installed")
        self.assertFalse(other._cssk_derived_codes())


class TestLoadBearingRowsAreLabelled(TransactionCase):
    """Labels, and the one block where a row number means two different things.

    Most DPPO rows carry no label and that is deliberate: this repository has
    no source for their statutory names, and a plausible-looking invented one
    is worse than a blank because it reads as authoritative.

    The rows that ARE labelled split in two:

    * outside the 800/900 block, a row means the same on every vzor — DPPO
      numbering is otherwise stable — so a label on one is a label on all;
    * inside it, the number was **reused**. r820 is the kladný rozdiel on the
      licencia vzory and something else once minimálna daň replaced it, and
      r900 moves from "Daňová licencia na úhradu" to "Suma na účely určenia
      výšky preddavkov". Those are labelled only where a source covers the
      vzor, and left bare everywhere else.

    That split is the whole lesson: an earlier version of this file asserted
    the first rule over the second and carried two wrong labels into the
    800-block, extrapolated from the v24/v25 spine onto vzory it does not
    describe. Finančná správa's own usmernenie prints those captions and
    disagreed.
    """

    # Where a row number was reused between the daňová licencia and the
    # minimálna daň eras. Nothing here may be assumed from another vzor.
    VOLATILE = ("r800", "r810", "r820", "r830", "r900")

    def _versions(self):
        versions = self.env["cssk.income.tax.version"].search(
            [("country_id.code", "=", "SK")])
        self.assertTrue(versions, "no SK DPPO versions seeded")
        return versions

    def test_a_stable_row_labelled_once_is_labelled_everywhere(self):
        versions = self._versions()
        labelled = {}
        for version in versions:
            for ldef in version.line_def_ids:
                if ldef.code in self.VOLATILE:
                    continue
                if ldef.name and ldef.name != ldef.code:
                    labelled.setdefault(ldef.code, ldef.name)
        self.assertTrue(labelled, "no stable DPPO row carries a label at all")

        missing = []
        for version in versions:
            for ldef in version.line_def_ids:
                if ldef.code in self.VOLATILE:
                    continue
                if ldef.code in labelled and ldef.name == ldef.code:
                    missing.append("%s/%s" % (version.name, ldef.code))
        self.assertFalse(
            missing,
            "labelled elsewhere but bare here: %s" % ", ".join(sorted(missing)))

    def test_a_stable_row_carries_the_same_label_everywhere(self):
        """Two spellings of one row would mean somebody guessed one of them."""
        seen = {}
        for version in self._versions():
            for ldef in version.line_def_ids:
                if ldef.code in self.VOLATILE or ldef.name == ldef.code:
                    continue
                seen.setdefault(ldef.code, set()).add(ldef.name)
        clashes = {c: sorted(n) for c, n in seen.items() if len(n) > 1}
        self.assertFalse(clashes, "one row, two labels: %s" % clashes)

    def test_the_provision_row_a_version_names_is_labelled(self):
        """``provision_line_code`` posts the year-end tax provision.

        A version field naming a row makes that row load-bearing by
        definition — somebody reading the booked entry has to be able to see
        which figure it came from.
        """
        for version in self._versions():
            code = version.provision_line_code
            if not code:
                continue
            ldef = version.line_def_ids.filtered(lambda d: d.code == code)
            self.assertEqual(
                len(ldef), 1,
                "%s: provision_line_code %s names no line" % (version.name, code))
            self.assertNotEqual(
                ldef.name, ldef.code,
                "%s: the provision row %s is unlabelled" % (version.name, code))

    def test_no_era_label_leaks_into_the_other_era(self):
        """Daňová licencia to 2017, minimálna daň from 2024 — same § 46b.

        Naming a licencia-era row "minimálna daň" would misname a figure that
        was filed under a levy of a different name, and the two eras differ by
        more than wording: the row numbers were reused.
        """
        for version in self._versions():
            era_is_licencia = version.valid_from.year <= 2019
            for ldef in version.line_def_ids:
                if ldef.name == ldef.code:
                    continue
                low = ldef.name.lower()
                if era_is_licencia:
                    self.assertNotIn(
                        "minimálna daň", low,
                        "%s (%s): %s is named for the wrong era: %r"
                        % (version.name, version.valid_from, ldef.code, ldef.name))
                else:
                    self.assertNotIn(
                        "licenci", low,
                        "%s (%s): %s is named for the wrong era: %r"
                        % (version.name, version.valid_from, ldef.code, ldef.name))


@tagged("post_install", "-at_install")
class TestDppoSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copy is CURRENT — nothing local can answer that, which
    is the whole reason the pin file exists. Doubly so here: FS SR revises the
    DPPO under a NEW FILENAME (dppo2025_v2.xsd appeared beside an unchanged
    dppo2025.xsd), so even re-fetching the pinned name would report "no
    change" while a revision sat one URL away. See data/SCHEMA_VERSION. This checks the weaker thing that
    is still worth having: that the bundled bytes are the ones somebody
    verified against the published copy on a stated date. Replacing a schema
    then has to be a deliberate two-file change rather than a silent one, and
    the refresh procedure lives next to the digest that would have to move.
    """

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(data, name)
            self.assertTrue(os.path.exists(path), "%s is pinned but missing" % name)
            blob = open(path, "rb").read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(), digest,
                "%s does not match its pin — if this is a deliberate refresh, "
                "update data/SCHEMA_VERSION and re-run the export tests" % name)

    def test_every_bundled_schema_is_pinned(self):
        """A schema added without a pin is the gap this file exists to close."""
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        pinned = set()
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pinned.add(parts[0])
        self.assertEqual(on_disk, pinned,
                         "unpinned schema(s): %s" % sorted(on_disk - pinned))


@tagged("post_install", "-at_install")
class TestSkDppoVintages(AccountTestInvoicingCommon):
    """One version per vzor, 2013 onwards.

    A DPPO is filed on the tlačivo for its zdaňovacie obdobie, and FS SR keeps
    every one it has published. Until now the module carried two, so any period
    before 2024 resolved to no version at all — not a wrong figure but NO
    figure, the return refusing to compute. That matters for a dodatočné
    priznanie, which is exactly the case where an old period comes back.
    """

    #: xmlid suffix -> (schema, first year, last year)
    VINTAGES = (
        ("2013", "dppo2013.xsd", 2013, 2013),
        ("2014", "dppo2014.xsd", 2014, 2014),
        # No dppo2016 exists: 2016 is filed on the 2015 vzor.
        ("2015", "dppo2015.xsd", 2015, 2016),
        ("2017", "dppo2017.xsd", 2017, 2017),
        ("2018", "dppo2018.xsd", 2018, 2018),
        ("2019", "dppo2019.xsd", 2019, 2019),
        ("2020", "dppo2020.xsd", 2020, 2020),
        ("2021", "dppo2021.xsd", 2021, 2021),
        # No dppo2023 either: 2023 is filed on the 2022 vzor, which is why the
        # 2022 poučenie ships separate instructions for rok 2022 and rok 2023.
        ("2022", "dppo2022.xsd", 2022, 2023),
        ("2024", "dppo2024.xsd", 2024, 2024),
        ("2025", "dppo2025_v2.xsd", 2025, 2025),
    )

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"
        cls.company.company_registry = "36000001"
        cls.company.write({"city": "Bratislava", "zip": "81101",
                           "street": "Test 1"})

    def _version(self, suffix):
        return self.env.ref("l10n_sk_dppo.dppo_version_%s" % suffix)

    def test_every_published_vzor_has_a_version(self):
        for suffix, schema, first, last in self.VINTAGES:
            version = self._version(suffix)
            self.assertEqual(version.country_id.code, "SK")
            self.assertEqual(version.xml_root_element, "dokument")
            self.assertEqual(version.xml_schema_filename, schema)
            self.assertTrue(version.xml_schema_data, "%s XSD not loaded" % suffix)
            self.assertEqual(str(version.valid_from), "%d-01-01" % first)
            self.assertEqual(str(version.valid_to), "%d-12-31" % last)
            self.assertEqual(len(version.statement_type_ids), 3)

    def test_the_vintages_tile_every_year_since_2013(self):
        """No year without a vzor, and no year with two.

        2016 and 2023 are the interesting ones: FS SR published no schema for
        either, and they are filed on the preceding vzor rather than being
        gaps.
        """
        sk = self.env.ref("base.sk")
        expected = {}
        for suffix, _schema, first, last in self.VINTAGES:
            for year in range(first, last + 1):
                expected[year] = suffix
        for year, suffix in sorted(expected.items()):
            found = self.env["cssk.income.tax.version"].search([
                ("country_id", "=", sk.id),
                ("valid_from", "<=", "%d-12-31" % year),
                "|", ("valid_to", "=", False), ("valid_to", ">=", "%d-01-01" % year),
            ])
            self.assertEqual(len(found), 1,
                             "%d resolves to %d versions" % (year, len(found)))
            self.assertEqual(found, self._version(suffix),
                             "%d reached the wrong vzor" % year)

    def test_each_vintage_defines_exactly_its_schema_s_rows(self):
        """Both directions, per vintage.

        A row the XSD has and the version lacks never gets computed; a row the
        version has and the XSD lacks would file on a row that did not exist
        in that year. Only the nine generated vintages are checked — the 2024
        and 2025 records were written by hand and carry a deliberate subset.
        """
        import re

        from odoo.tools.misc import file_path

        generated = [v for v in self.VINTAGES if v[0] not in ("2024", "2025")]
        for suffix, schema, _first, _last in generated:
            with open(file_path("l10n_sk_dppo/data/%s" % schema),
                      encoding="utf-8", errors="replace") as handle:
                rows = set(re.findall(r'<xsd:element\s+name="(r\d+[a-z]?)"',
                                      handle.read()))
            codes = set(self._version(suffix).line_def_ids.mapped("code"))
            self.assertEqual(rows - codes, set(),
                             "%s defines rows %s never computes" % (schema, suffix))
            self.assertEqual(codes - rows, set(),
                             "%s computes rows %s does not have" % (suffix, schema))

    #: Every vintage now carries its § 15 rate. 2020 onwards from the vzor's
    #: own poučenie; 2015-2019 sourced separately, because those forms ask for
    #: the rate rather than printing it (r550 is an entry field, since a
    #: hospodársky rok can straddle a change). 2013 and 2014 have no rate row
    #: at all and need none.
    RATED = {"2015", "2017", "2018", "2019",
             "2020", "2021", "2022", "2024", "2025"}
    #: The rate each vintage must carry, so a transcription slip in the
    #: generator fails here rather than in somebody's tax.
    EXPECTED_RATE = {
        "2015": 22.0, "2017": 21.0, "2018": 21.0, "2019": 21.0,
        "2020": 21.0, "2021": 21.0, "2022": 21.0, "2024": 21.0,
    }

    def _return_for(self, suffix, year):
        version = self._version(suffix)
        type_r = version.statement_type_ids.filtered(
            lambda t: t.fa_xml_value == "R")
        return self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": version.id,
            "statement_type_id": type_r.id,
            "date_from": "%d-01-01" % year, "date_to": "%d-12-31" % year,
        })

    def test_each_vintage_carries_the_rate_that_applied_that_year(self):
        """The standard § 15 písm. b) rate, pinned per vintage.

        22 % for 2015-2016, 21 % from 1. 1. 2017 and unchanged through 2019,
        after which the 15 % reduced band arrives. Pinned because the figure
        reaches a filed return through `r550`, and a slip in the generator's
        table would otherwise surface as somebody's tax rather than as a test.
        """
        for suffix, rate in sorted(self.EXPECTED_RATE.items()):
            bands = self._version(suffix).rate_bands
            self.assertTrue(bands, "%s carries no rate bands" % suffix)
            top = bands[-1]
            self.assertIsNone(top[0],
                              "%s: the last band must be open-ended" % suffix)
            self.assertEqual(top[1], rate, "%s standard rate" % suffix)

    def test_the_2015_vzor_rate_covers_2016_too(self):
        """One vzor, two years, and the rate did not move between them.

        A vintage spanning two years can only carry one rate, so it is only
        correct while the rate holds across both. 2015 and 2016 were both
        22 %; if a future vintage spans a change, it cannot be modelled this
        way and the bands would have to move to the period.
        """
        version = self._version("2015")
        self.assertEqual(str(version.valid_from), "2015-01-01")
        self.assertEqual(str(version.valid_to), "2016-12-31")
        self.assertEqual(version.rate_bands[-1][1], 22.0)

    def test_a_vintage_without_a_documented_rate_refuses_to_guess(self):
        """A vzor that ASKS for the § 15 rate must not have one invented.

        The 2013 and 2014 vzory have no rate row at all; r550 arrives in 2015
        and the banded r560 only in 2020, when the 15 % reduced rate was
        introduced. So the question only applies to a vintage that has r550 —
        and for 2015-2019 nothing written down says what the flat rate was:
        the poučenie says "sadzba dane podľa § 15 písm. b)" and leaves it to
        the taxpayer. ``rate_bands`` is deliberately empty there, and the
        module raises rather than computing somebody's tax from a rate recited
        from memory.
        """
        for suffix, _schema, first, _last in self.VINTAGES:
            version = self._version(suffix)
            has_rate_row = "r550" in version.line_def_ids.mapped("code")
            if version.rate_bands or not has_rate_row:
                continue
            with self.assertRaises(UserError, msg=suffix) as caught:
                self._return_for(suffix, first).action_compute_lines()
            self.assertIn("Refusing to guess", str(caught.exception))

    def test_every_vintage_exports_a_document_its_own_schema_accepts(self):
        """The check the row lists cannot make.

        The templates are generated from the schemas, so element ORDER and
        nesting come from the vzor itself — but a generator can still be wrong
        about what a field must CONTAIN. The vzor's own rate is printed as a
        fixed literal (fix15, fix21, "19"), several rows are a REQUIRED
        decimal where an empty element is rejected, an optional repeating
        table must be ABSENT rather than present-and-empty, and some rows are
        an INTEGER union that "0.00" is not a valid value of. Every one was a
        real failure before it was fixed, and only an export catches them.

        A vintage with no documented rate has one supplied HERE, by the test,
        so that everything except that one statutory number is exercised. The
        21 % is the test's input and not a claim about the year.
        """
        import base64

        from lxml import etree

        for suffix, _schema, first, _last in self.VINTAGES:
            version = self._version(suffix)
            if not version.rate_bands:
                version.rate_bands = [[None, 21.0]]
            ret = self._return_for(suffix, first)
            ret.action_compute_lines()
            ret.action_export_xml()
            self.assertEqual(ret.state, "exported", suffix)
            root = etree.fromstring(
                base64.b64decode(ret.xml_attachment_id.datas))
            self.assertEqual(etree.QName(root).localname, "dokument", suffix)

    def test_the_2025_vzor_files_against_the_revision(self):
        """dppo2025_v2.xsd, not dppo2025.xsd.

        FS SR published a revision under a NEW NAME beside an unchanged
        original — v2 adds a repeatable `dalsiaTransakcia` and is otherwise the
        same file. A digest check on the pinned name would report "no change"
        forever while the revision sat one URL away. Being a superset, v2
        accepts every document the original did, so filing against it is
        strictly safer.
        """
        import hashlib

        from odoo.tools.misc import file_path

        self.assertEqual(self._version("2025").xml_schema_filename,
                         "dppo2025_v2.xsd")
        digests = {}
        for schema in ("dppo2025.xsd", "dppo2025_v2.xsd"):
            with open(file_path("l10n_sk_dppo/data/%s" % schema), "rb") as fh:
                digests[schema] = hashlib.md5(fh.read()).hexdigest()
        self.assertNotEqual(digests["dppo2025.xsd"], digests["dppo2025_v2.xsd"])
