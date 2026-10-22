import base64

from lxml import etree

from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkFs(TransactionCase):
    """Smoke tests for the SK Súvaha country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_fs.suvaha_version_2025")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.statement_kind, "balance_sheet")
        self.assertEqual(version.xml_root_element, "UZSUV")
        self.assertTrue(version.xml_schema_data, "Súvaha XSD not loaded")
        codes = set(version.line_def_ids.mapped("code"))
        self.assertIn("SPOLU_M", codes)
        self.assertIn("SPOLU_VI", codes)
        vzs = self.env.ref("l10n_sk_fs.vzs_version_2025")
        self.assertEqual(vzs.statement_kind, "profit_loss")
        self.assertEqual(vzs.xml_root_element, "UZVZS")


@tagged("post_install", "-at_install")
class TestSkFsCompute(AccountTestInvoicingCommon):
    """Functional: post a balanced entry, compute + export the Súvaha."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava"})
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.acc_asset = cls.env["account.account"].create({
            "name": "DHM", "code": "022999",
            "account_type": "asset_non_current",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.acc_eq = cls.env["account.account"].create({
            "name": "Základné imanie", "code": "411999",
            "account_type": "equity",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.acc_rev = cls.env["account.account"].create({
            "name": "Tržby", "code": "602999", "account_type": "income",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.acc_exp = cls.env["account.account"].create({
            "name": "Spotreba", "code": "501999", "account_type": "expense",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.acc_bank = cls.env["account.account"].create({
            "name": "Banka", "code": "221999", "account_type": "asset_current",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.version = cls.env.ref("l10n_sk_fs.suvaha_version_2025")
        cls.vzs_version = cls.env.ref("l10n_sk_fs.vzs_version_2025")

    def test_compute_and_export(self):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.acc_asset.id,
                        "debit": 1000.0, "credit": 0.0}),
                (0, 0, {"account_id": self.acc_eq.id,
                        "debit": 0.0, "credit": 1000.0}),
            ],
        })
        move.action_post()

        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        rows = {line.code: line.current_value for line in st.line_ids}
        self.assertAlmostEqual(rows["A"], 1000.0, places=2)        # asset (022)
        self.assertAlmostEqual(rows["VI"], 1000.0, places=2)       # equity (411, negated)
        self.assertAlmostEqual(rows["SPOLU_M"], 1000.0, places=2)  # total assets
        # The balance sheet balances: assets == equity + liabilities.
        self.assertAlmostEqual(rows["SPOLU_M"], rows["SPOLU_VI"], places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "UZSUV")
        riadky = {r.get("kod"): r.get("bezne")
                  for r in root.findall(".//Riadok")}
        self.assertEqual(riadky["SPOLU_M"], "1000.00")

    def test_cash_flow_reconciles(self):
        """Prehľad peňažných tokov (indirect): A+B+C = D = closing − opening
        cash; the partition reconciles by construction (G = 0)."""
        loan = self.env["account.account"].create({
            "name": "Bankový úver", "code": "461999",
            "account_type": "liability_non_current",
            "company_ids": [(6, 0, [self.company.id])]})
        J = self.journal.id

        def entry(date, lines):
            self.env["account.move"].create({
                "move_type": "entry", "journal_id": J, "date": date,
                "line_ids": [(0, 0, ln) for ln in lines]}).action_post()

        # sale paid to bank (+1000 operating)
        entry("2026-03-10", [{"account_id": self.acc_bank.id, "debit": 1000.0},
                             {"account_id": self.acc_rev.id, "credit": 1000.0}])
        # buy a machine (−600 investing)
        entry("2026-04-10", [{"account_id": self.acc_asset.id, "debit": 600.0},
                             {"account_id": self.acc_bank.id, "credit": 600.0}])
        # draw a loan (+300 financing)
        entry("2026-05-10", [{"account_id": self.acc_bank.id, "debit": 300.0},
                             {"account_id": loan.id, "credit": 300.0}])

        cf = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_fs.cashflow_version_2025").id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        cf.action_compute_lines()
        v = {l.code: l.current_value for l in cf.line_ids}
        self.assertAlmostEqual(v["A"], 1000.0, 2)   # prevádzková
        self.assertAlmostEqual(v["B"], -600.0, 2)   # investičná
        self.assertAlmostEqual(v["C"], 300.0, 2)    # finančná
        self.assertAlmostEqual(v["D"], 700.0, 2)    # čistá zmena PP
        self.assertAlmostEqual(v["E"], 0.0, 2)      # stav na začiatku
        self.assertAlmostEqual(v["F"], 700.0, 2)    # stav na konci
        self.assertAlmostEqual(v["G"], 0.0, 2)      # kontrola E+D−F=0
        cf.action_export_xml()                       # renders, no official XSD
        self.assertEqual(cf.state, "exported")

    def test_changes_in_equity_reconciles(self):
        """Prehľad zmien VI: opening + Σ component changes = closing equity
        (incl. the current-period result); G = 0 by construction."""
        J = self.journal.id

        def entry(date, lines):
            self.env["account.move"].create({
                "move_type": "entry", "journal_id": J, "date": date,
                "line_ids": [(0, 0, ln) for ln in lines]}).action_post()

        # capital increase (+10000 equity)
        entry("2026-01-15", [{"account_id": self.acc_bank.id, "debit": 10000.0},
                             {"account_id": self.acc_eq.id, "credit": 10000.0}])
        # profit for the year (+2000 current result)
        entry("2026-06-30", [{"account_id": self.acc_bank.id, "debit": 2000.0},
                             {"account_id": self.acc_rev.id, "credit": 2000.0}])

        eq = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_fs.equity_changes_version_2025").id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        eq.action_compute_lines()
        v = {l.code: l.current_value for l in eq.line_ids}
        self.assertAlmostEqual(v["ZI"], 10000.0, 2)    # základné imanie
        self.assertAlmostEqual(v["VHO"], 2000.0, 2)    # výsledok bežného obdobia
        self.assertAlmostEqual(v["ZMENA"], 12000.0, 2)
        self.assertAlmostEqual(v["E"], 0.0, 2)         # opening equity
        self.assertAlmostEqual(v["F"], 12000.0, 2)     # closing equity (incl. result)
        self.assertAlmostEqual(v["G"], 0.0, 2)         # kontrola E+B−C=0

    def test_submit_lock_and_retention(self):
        """Submitting an účtovná závierka freezes the filed XML and locks it;
        reset keeps the filed copy."""
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.acc_asset.id, "debit": 1000.0}),
                (0, 0, {"account_id": self.acc_eq.id, "credit": 1000.0}),
            ],
        })
        move.action_post()
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31"})
        st.action_compute_lines()
        st.action_export_xml()
        filed = st.xml_attachment_id

        st.submission_reference = "FS-ZB-2026-001"
        st.action_submit()
        self.assertEqual(st.state, "submitted")
        self.assertEqual(st.submitted_attachment_id, filed)
        self.assertTrue(st.submitted_date)
        with self.assertRaises(UserError):
            st.action_export_xml()
        with self.assertRaises(UserError):
            st.action_compute_lines()
        st.action_reset_to_draft()
        self.assertEqual(st.state, "draft")
        self.assertEqual(st.submitted_attachment_id, filed)

    def test_vzs_compute_and_export(self):
        # P&L uses the period movement (not cumulative as-of).
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.acc_bank.id,
                        "debit": 1200.0, "credit": 0.0}),
                (0, 0, {"account_id": self.acc_rev.id,
                        "debit": 0.0, "credit": 2000.0}),
                (0, 0, {"account_id": self.acc_exp.id,
                        "debit": 800.0, "credit": 0.0}),
            ],
        })
        move.action_post()

        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.vzs_version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        rows = {line.code: line.current_value for line in st.line_ids}
        # II = tržby z vlastných výrobkov/služieb (602); B = spotreba (501)
        self.assertAlmostEqual(rows["II"], 2000.0, places=2)
        self.assertAlmostEqual(rows["B"], 800.0, places=2)
        self.assertAlmostEqual(rows["PREV"], 1200.0, places=2)   # prevádzkový VH
        self.assertAlmostEqual(rows["VHU"], 1200.0, places=2)    # VH za obdobie

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "UZVZS")
        riadky = {r.get("kod"): r.get("bezne")
                  for r in root.findall(".//Riadok")}
        self.assertEqual(riadky["VHU"], "1200.00")

    def test_suvaha_reconciles_with_current_result(self):
        """Súvaha ties out with a current-year result: bank +1200, revenue
        2000, expense 800 -> A.V (PAV) = 1200 balances the sheet."""
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.acc_bank.id, "debit": 1200.0}),
                (0, 0, {"account_id": self.acc_rev.id, "credit": 2000.0}),
                (0, 0, {"account_id": self.acc_exp.id, "debit": 800.0}),
            ],
        })
        move.action_post()
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        rows = {line.code: line.current_value for line in st.line_ids}
        self.assertAlmostEqual(rows["PAV"], 1200.0, places=2)       # current result
        self.assertAlmostEqual(rows["SPOLU_M"], 1200.0, places=2)   # bank
        self.assertAlmostEqual(rows["SPOLU_M"], rows["SPOLU_VI"], places=2)
