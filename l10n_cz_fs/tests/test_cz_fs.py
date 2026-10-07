# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzFs(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        # l10n_cz_statutory, where it is installed alongside, adds a preflight
        # that every Czech submission carry its finanční úřad code (c_ufo).
        # This module does not depend on it, so the suite was green standalone
        # and red on any full-bundle install — which is every customer, since
        # the l10n_cz_datadance umbrella brings both. Production is right to
        # demand the office; the fixture simply never provided one.
        if not cls.company.l10n_cssk_tax_authority_id:
            authority = cls.env["cssk.tax.authority"].search(
                [("country_code", "=", "CZ")], limit=1)
            if not authority:
                authority = cls.env["cssk.tax.authority"].create({
                    "name": "FÚ pro hlavní město Prahu",
                    "code": "CZ-TEST-1",
                    "submission_code": "451",
                    "country_id": cls.env.ref("base.cz").id,
                })
            cls.company.l10n_cssk_tax_authority_id = authority
        cls.pl_version = cls.env.ref("l10n_cz_fs.vysledovka_version_2025")
        cls.bs_version = cls.env.ref("l10n_cz_fs.rozvaha_version_2025")
        cls.misc = cls.company_data["default_journal_misc"]
        # A single posted entry: revenue 5000 (602), cost 3000 (501),
        # bank +2000 (221). YTD result = 2000.
        income = cls._acc(cls, "602%")
        expense = cls._acc(cls, "501%")
        bank = cls._acc(cls, "221%")
        move = cls.env["account.move"].create({
            "move_type": "entry", "journal_id": cls.misc.id, "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": income.id, "credit": 5000.0}),
                Command.create({"account_id": expense.id, "debit": 3000.0}),
                Command.create({"account_id": bank.id, "debit": 2000.0}),
            ],
        })
        move.action_post()

    def _acc(self, like):
        return self.env["account.account"].search(
            [("code", "=like", like), ("company_ids", "in", self.company.id)],
            limit=1,
        )

    def _statement(self, version):
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31",
        })
        st.action_compute_lines()
        return st

    def _v(self, st, code):
        return st.line_ids.filtered(lambda l: l.code == code).current_value

    def test_profit_loss_full_lines_and_export(self):
        st = self._statement(self.pl_version)
        # I = revenue (601,602); A2 = material/energy (501-503); result lines.
        self.assertAlmostEqual(self._v(st, "I"), 5000.0, places=2)
        self.assertAlmostEqual(self._v(st, "A2"), 3000.0, places=2)
        self.assertAlmostEqual(self._v(st, "PROV"), 2000.0, places=2)
        self.assertAlmostEqual(self._v(st, "VHU"), 2000.0, places=2)
        self.assertAlmostEqual(self._v(st, "COBR"), 5000.0, places=2)
        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Vysledovka")

    def test_export_without_an_xsd_is_a_declared_state_not_a_hole(self):
        """The Czech statements have no published XSD, and that is the form.

        Rozvaha, VZZ and the two přehledy are filed as attachments inside the
        DPPO envelope; the Finanční správa publishes no standalone schema for
        any of them, while the Slovak Úč POD ships ``uzpod-2014.xsd``. So
        "no schema" is a property of the VERSION.

        The mixin was tightened to refuse an export it could not validate —
        right, and it broke every Czech FS export until the version could say
        the absence is deliberate. Both halves are asserted here: the flag
        permits the export, and clearing it brings the refusal straight back,
        so the narrowing cannot quietly widen into "never validate".
        """
        self.assertFalse(
            self.bs_version.xml_schema_data,
            "premise: no XSD is shipped for the Rozvaha")
        self.assertTrue(
            self.bs_version.xml_schema_optional,
            "the version must declare that absence")

        st = self._statement(self.bs_version)
        st.action_export_xml()
        self.assertEqual(st.state, "exported")

        self.bs_version.xml_schema_optional = False
        blocked = self._statement(self.bs_version)
        with self.assertRaises(UserError) as cm:
            blocked.action_export_xml()
        self.assertIn("no XML schema", str(cm.exception))

    def test_balance_sheet_reconciles(self):
        """AKTIVA must equal PASIVA — the proof that the account partition is
        complete and the current-year result (A.V) ties the sheet out."""
        st = self._statement(self.bs_version)
        aktiva = self._v(st, "AKTIVA")
        pasiva = self._v(st, "PASIVA")
        self.assertAlmostEqual(aktiva, 2000.0, places=2)   # bank +2000
        self.assertAlmostEqual(self._v(st, "AV"), 2000.0, places=2)  # YTD result
        self.assertAlmostEqual(aktiva, pasiva, places=2)   # ties out
        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Rozvaha")

    def test_aktiva_carry_brutto_and_korekce(self):
        """The Rozvaha is filed in brutto / korekce / netto columns (DPPDP9
        VetaUA), so the oprávky and opravné položky must stay a column of the
        row rather than be netted into it — with netto what it always was,
        and the row's documents still adding up to it. 094 (OP k
        nedokončenému DHM) is B.II., not B.I."""
        def entry(lines):
            self.env["account.move"].create({
                "move_type": "entry", "journal_id": self.misc.id,
                "date": "2025-09-30",
                "line_ids": [Command.create({"account_id": self._acc(a).id,
                                             "debit": d, "credit": c})
                             for a, d, c in lines]}).action_post()

        entry([("022%", 1000.0, 0.0), ("082%", 0.0, 300.0),
               ("094%", 0.0, 50.0), ("221%", 0.0, 650.0)])
        st = self._statement(self.bs_version)
        bii = st.line_ids.filtered(lambda l: l.code == "BII")
        self.assertAlmostEqual(bii.gross_value, 1000.0, places=2)
        self.assertAlmostEqual(bii.correction_value, 350.0, places=2)
        self.assertAlmostEqual(bii.current_value, 650.0, places=2)
        self.assertTrue(bii.source_reconciles,
                        "the row's documents include its oprávky")
        self.assertAlmostEqual(self._v(st, "BI"), 0.0, places=2)
        self.assertAlmostEqual(self._v(st, "AKTIVA"),
                               self._v(st, "PASIVA"), places=2)

    def test_cash_flow_reconciles(self):
        """Přehled o peněžních tocích (nepřímá metoda): A+B+C = F = konec −
        začátek; the partition reconciles by construction (G = 0). The setUpClass
        entry (revenue 5000 / cost 3000 / bank +2000) sits in provozní činnost."""
        bank = self._acc("221%")
        revenue = self._acc("602%")
        asset = self.env["account.account"].create({
            "name": "Stroj", "code": "022900",
            "account_type": "asset_non_current",
            "company_ids": [(6, 0, [self.company.id])]})
        loan = self.env["account.account"].create({
            "name": "Bankovní úvěr", "code": "461900",
            "account_type": "liability_non_current",
            "company_ids": [(6, 0, [self.company.id])]})

        def entry(date, lines):
            self.env["account.move"].create({
                "move_type": "entry", "journal_id": self.misc.id, "date": date,
                "line_ids": [Command.create(ln) for ln in lines]}).action_post()

        # sale collected to bank (+1000 provozní)
        entry("2025-03-10", [{"account_id": bank.id, "debit": 1000.0},
                             {"account_id": revenue.id, "credit": 1000.0}])
        # buy a machine (−600 investiční)
        entry("2025-04-10", [{"account_id": asset.id, "debit": 600.0},
                             {"account_id": bank.id, "credit": 600.0}])
        # draw a loan (+300 finanční)
        entry("2025-05-10", [{"account_id": bank.id, "debit": 300.0},
                             {"account_id": loan.id, "credit": 300.0}])

        cf = self._statement(self.env.ref("l10n_cz_fs.cashflow_version_2025"))
        v = {l.code: l.current_value for l in cf.line_ids}
        self.assertAlmostEqual(v["A"], 3000.0, 2)   # provozní (2000 setUp + 1000)
        self.assertAlmostEqual(v["B"], -600.0, 2)   # investiční
        self.assertAlmostEqual(v["C"], 300.0, 2)    # finanční
        self.assertAlmostEqual(v["F"], 2700.0, 2)   # čistá změna PP
        self.assertAlmostEqual(v["P"], 0.0, 2)      # stav na začátku
        self.assertAlmostEqual(v["R"], 2700.0, 2)   # stav na konci
        self.assertAlmostEqual(v["G"], 0.0, 2)      # kontrola P+F−R=0
        cf.action_export_xml()                       # renders, no official XSD
        self.assertEqual(cf.state, "exported")
        root = etree.fromstring(base64.b64decode(cf.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "PrehledPT")

    def test_changes_in_equity_reconciles(self):
        """Přehled o změnách vlastního kapitálu: počátek + Σ změny = konec
        (incl. the current-period result); G = 0 by construction."""
        bank = self._acc("221%")
        zk = self._acc("411%")

        def entry(date, lines):
            self.env["account.move"].create({
                "move_type": "entry", "journal_id": self.misc.id, "date": date,
                "line_ids": [Command.create(ln) for ln in lines]}).action_post()

        # capital increase (+10000 základní kapitál)
        entry("2025-01-15", [{"account_id": bank.id, "debit": 10000.0},
                             {"account_id": zk.id, "credit": 10000.0}])

        eq = self._statement(self.env.ref("l10n_cz_fs.equity_changes_version_2025"))
        v = {l.code: l.current_value for l in eq.line_ids}
        self.assertAlmostEqual(v["ZK"], 10000.0, 2)     # základní kapitál
        self.assertAlmostEqual(v["VHB"], 2000.0, 2)     # VH běžného období (setUp)
        self.assertAlmostEqual(v["ZMENY"], 12000.0, 2)
        self.assertAlmostEqual(v["POC"], 0.0, 2)        # počátek
        self.assertAlmostEqual(v["KON"], 12000.0, 2)    # konec (incl. result)
        self.assertAlmostEqual(v["G"], 0.0, 2)          # kontrola A+B−C=0
        eq.action_export_xml()
        root = etree.fromstring(base64.b64decode(eq.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "PrehledVK")

    def test_opravna_zaverka_amendment(self):
        """Opravná účetní závěrka: submit a Rozvaha, raise an amendment — it
        links back to the original, is flagged Opravná, keeps the filed copy,
        and recomputes + exports with the corrective marker in the header."""
        st = self._statement(self.bs_version)
        self.assertEqual(st.submission_type, "radna")
        st.action_export_xml()
        st.submission_reference = "FS-CZ-2025-001"
        st.action_submit()
        self.assertEqual(st.state, "submitted")
        filed = st.submitted_attachment_id

        action = st.action_create_amendment()
        amend = self.env["cssk.fs.statement"].browse(action["res_id"])
        # linked, flagged, fresh draft without a carried-over filed XML
        self.assertEqual(amend.original_return_id, st)
        self.assertEqual(amend.submission_type, "opravna")
        self.assertEqual(amend.state, "draft")
        self.assertFalse(amend.xml_attachment_id)
        # the suffix's source msgid is English "(corrective)" — asserting the
        # Czech rendering only works with cs_CZ loaded + active
        self.assertIn("corrective", amend.name)
        self.assertEqual(amend.amendment_ids, self.env["cssk.fs.statement"])
        self.assertIn(amend, st.amendment_ids)
        # original is untouched: still submitted, filed copy preserved
        self.assertEqual(st.state, "submitted")
        self.assertEqual(st.submitted_attachment_id, filed)

        # the amendment is a full restatement that still reconciles + exports
        amend.action_compute_lines()
        self.assertAlmostEqual(self._v(amend, "AKTIVA"),
                               self._v(amend, "PASIVA"), places=2)
        amend.action_export_xml()
        root = etree.fromstring(base64.b64decode(amend.xml_attachment_id.datas))
        self.assertEqual(root.findtext(".//TypZaverky"), "opravna")
