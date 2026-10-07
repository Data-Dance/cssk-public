import base64

from lxml import etree

from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkFs(TransactionCase):
    """Smoke tests for the SK Súvaha country layer (run at install)."""

    def test_version_seeded(self):
        """One version, the whole závierka, against the official schema."""
        version = self.env.ref("l10n_sk_fs.uzpod_v14")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "dokument")
        self.assertTrue(version.xml_schema_data, "UZPODv14 XSD not loaded")
        codes = version.line_def_ids.mapped("code")
        self.assertEqual(len(codes), 206, "145 súvaha + 61 výkaz rows")
        self.assertEqual(len([c for c in codes if c.startswith("s")]), 145)
        self.assertEqual(len([c for c in codes if c.startswith("v")]), 61)
        self.assertEqual(len(set(codes)), len(codes), "codes must be unique")

    def test_the_two_blocks_read_different_bases(self):
        """The reason `basis` exists: one document, two bases.

        The súvaha reports the cumulative balance as of the period end and the
        výkaz the movement within it. A single ``statement_kind`` cannot say
        that, so before ``basis`` these had to be two version records — and
        two records cannot produce the one ``dokument`` the form is.
        """
        version = self.env.ref("l10n_sk_fs.uzpod_v14")
        suvaha = version.line_def_ids.filtered(lambda d: d.code.startswith("s"))
        vykaz = version.line_def_ids.filtered(lambda d: d.code.startswith("v"))
        # A.VIII is the exception, and deliberately: the current-year result is
        # the MOVEMENT of triedy 5/6, so that it equals VZS r61 even when last
        # year's classes have not yet been closed to účet 431. Reading it as a
        # cumulative balance would report 0 on an open ledger.
        self.assertEqual(
            {d.code for d in suvaha if d._cssk_reads_movement()}, {"s100"})
        self.assertTrue(all(d._cssk_reads_movement() for d in vykaz))

    def test_the_korekcia_column_is_modelled(self):
        """52 súvaha rows are filed brutto / korekcia / netto.

        ``tRiadok14`` requires s1/s2/s3/s4, so a row that stores only a net
        figure cannot be filed. The tlačivo states both groups per row —
        r005 Softvér is "(013) - /073, 091A/".
        """
        version = self.env.ref("l10n_sk_fs.uzpod_v14")
        with_corr = version.line_def_ids.filtered("account_formula_correction")
        self.assertGreaterEqual(len(with_corr), 50)
        softver = version.line_def_ids.filtered(lambda d: d.code == "s005")
        # Specific chart codes, not 3-digit groups: the leaves are generated
        # from the filed export's mapping so the screen and the XML cannot
        # drift apart. See test_uzpod_one_mapping.
        self.assertEqual(softver.account_formula, "013000")
        self.assertEqual(softver.account_formula_correction, "073000,091200")


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
        cls.version = cls.env.ref("l10n_sk_fs.uzpod_v14")

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
        self.assertAlmostEqual(rows["s002"], 1000.0, places=2)        # asset (022)
        self.assertAlmostEqual(rows["s080"], 1000.0, places=2)       # equity (411, negated)
        self.assertAlmostEqual(rows["s001"], 1000.0, places=2)  # total assets
        # The balance sheet balances: assets == equity + liabilities.
        self.assertAlmostEqual(rows["s001"], rows["s079"], places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        # rows are emitted as <rNNN><s1>..</s1>…, per tRiadok14/12
        self.assertTrue(root.find(".//ucPod1Suvaha") is not None)
        self.assertTrue(root.find(".//ucPod2VykazZS") is not None)

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
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        rows = {line.code: line.current_value for line in st.line_ids}
        # II = tržby z vlastných výrobkov/služieb (602); B = spotreba (501)
        self.assertAlmostEqual(rows["v05"], 2000.0, places=2)
        self.assertAlmostEqual(rows["v12"], 800.0, places=2)
        # v27 *** Výsledok hospodárenia z hospodárskej činnosti = v02 - v10
        self.assertAlmostEqual(rows["v27"], 1200.0, places=2)
        # v61 **** VH za účtovné obdobie po zdanení = v56 - v57 - v60
        self.assertAlmostEqual(rows["v61"], 1200.0, places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        # rows are emitted as <rNNN><s1>..</s1>…, per tRiadok14/12
        self.assertTrue(root.find(".//ucPod1Suvaha") is not None)
        self.assertTrue(root.find(".//ucPod2VykazZS") is not None)

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
        self.assertAlmostEqual(rows["s100"], 1200.0, places=2)       # current result
        self.assertAlmostEqual(rows["s001"], 1200.0, places=2)   # bank
        self.assertAlmostEqual(rows["s001"], rows["s079"], places=2)

    def test_a_two_sided_account_lands_on_one_side_only(self):
        """481 is a deferred tax ASSET in debit and a LIABILITY in credit.

        UZPODv14 names 481000 twice — r052 (A.III.11 odložená daňová
        pohľadávka) and, negated, r117 (B.I.12 odložený daňový záväzok) — and
        says nothing about which one a given balance belongs to, because the
        sign is what says it. Summed ungated the same balance lands on both
        rows at once: a company owing deferred tax would show the liability
        AND a negative asset of the same size.

        Nothing in the sheet objects to that. It still foots and, while A.VIII
        was a plug, it still balanced — which is how the whole class of error
        went unnoticed until the two mappings of this form were compared.
        """
        # ``code`` is per-company in 19.0 (a jsonb code_store keyed by
        # company), so the account has to be looked up in the test company's
        # own context — without with_company the code resolves against the env
        # company and finds a DIFFERENT company's 481000, whose balance never
        # reaches this statement.
        deferred = self.env["account.account"].with_company(self.company).search(
            [("code", "=", "481000"),
             ("company_ids", "in", self.company.id)], limit=1)
        self.assertTrue(deferred, "481000 missing from the SK chart")
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.acc_bank.id, "debit": 3000.0}),
                (0, 0, {"account_id": deferred.id, "credit": 3000.0}),
            ],
        })
        move.action_post()
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        rows = {line.code: line.current_value for line in st.line_ids}
        self.assertAlmostEqual(rows["s117"], 3000.0, places=2)  # the záväzok
        self.assertAlmostEqual(rows["s052"], 0.0, places=2)     # and NOT an asset
        self.assertAlmostEqual(rows["s001"], rows["s079"], places=2)

    def test_every_two_sided_prefix_is_derived_from_the_form(self):
        """The gated set is read off the definitions, not maintained by hand.

        Each of these is an account the osnova genuinely puts on either side by
        the sign of its balance — 341-347 daňové účty, 336 sociálne poistenie,
        316 čistá hodnota zákazky, 373 deriváty, 398 spojovací účet, 481
        odložená daň. If this list changes, the tlačivo transcription changed
        with it, and that is worth looking at rather than re-pinning.
        """
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        self.assertEqual(
            st._cssk_two_sided_prefixes(),
            {"341", "342", "343", "345", "346", "347",
             "316000", "316100", "336000", "373000", "373100",
             "398000", "398100", "481000"},
        )

    def test_an_account_no_row_claims_is_reported(self):
        """The failure a balanced sheet cannot show you.

        UZPODv14's rows name specific chart codes, so a company whose chart
        puts receivables somewhere the mapping never heard of loses that money
        from the statement entirely — and the statement still foots, still
        balances, and looks right. Nothing detects it from inside; it has to
        be reported.
        """
        stray = self.env["account.account"].with_company(self.company).create({
            "name": "Nezaradený účet", "code": "899123",
            "account_type": "asset_current",
            "company_ids": [(6, 0, [self.company.id])],
        })
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": stray.id, "debit": 4321.0}),
                (0, 0, {"account_id": self.acc_rev.id, "credit": 4321.0}),
            ],
        })
        move.action_post()
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        st.action_compute_lines()
        self.assertEqual(st.unmapped_count, 1)
        self.assertIn("899123", st.unmapped_note)
        self.assertEqual(st.unmapped_line_ids.account_ids, stray)
        self.assertEqual(st.action_view_unmapped()["res_id"], st.id)


@tagged("post_install", "-at_install")
class TestSkFsSchemaPins(TransactionCase):
    """The bundled schema must match data/SCHEMA_VERSION.

    Not a check that our copy is CURRENT — nothing local can answer that, and
    UZPODv14 is the worst case for trying: the file stamps itself only
    "Suvaha" and carries no revision, so a silently revised copy and a stale
    one are byte-indistinguishable from inside. What this checks is the weaker
    thing still worth having — that the bundled bytes are the ones somebody
    verified against the published copy on a stated date, so replacing the
    schema is a deliberate two-file change.

    This module is exactly why the check exists: until 19.0.1.1.0 it shipped
    two HAND-WRITTEN schemas (uzsuv/uzvzs) whose root elements FS SR has never
    published, and every export validated against them cleanly.
    """

    def _pins(self, data):
        import os
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def _data_dir(self):
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(here, "data")

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        data = self._data_dir()
        pins = self._pins(data)
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
        data = self._data_dir()
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(self._pins(data)),
                         "unpinned schema(s): %s"
                         % sorted(on_disk - set(self._pins(data))))


@tagged("post_install", "-at_install")
class TestUzpodFootprint(AccountTestInvoicingCommon):
    """The reverse drill must answer for BOTH columns of a row.

    A posting on an oprávky account feeds a row's KOREKCIA column, and until
    now the footprint read only the base formula and answered "this feeds
    nothing". 51 UZPODv14 rows carry a correction formula; 073000 appears in
    that version once as a correction and never as a base, so software
    depreciation — an entirely ordinary posting — reported no row at all.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava"})
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)],
            limit=1)

    def _account(self, code):
        acc = self.env["account.account"].with_company(self.company).search(
            [("code", "=", code), ("company_ids", "in", self.company.id)],
            limit=1)
        if not acc:
            self.skipTest("%s is not in this chart" % code)
        return acc

    def _post(self, debit_code, credit_code, amount=500.0):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self._account(debit_code).id,
                        "debit": amount}),
                (0, 0, {"account_id": self._account(credit_code).id,
                        "credit": amount}),
            ],
        })
        move.action_post()
        return move

    def test_a_korekcia_account_reports_the_row_it_feeds(self):
        """073000 feeds r005's korekcia and must say so."""
        move = self._post("551000", "073000")
        line = move.line_ids.filtered(
            lambda l: l.account_id.code == "073000")
        footprint = line._cssk_statutory_footprint()
        codes = [fp["code"] for fp in footprint]
        self.assertIn(
            "s005", codes,
            "oprávky k softvéru feed r005; the footprint read only the base "
            "formula and answered nothing: %s" % codes)
        korekcia = [fp for fp in footprint if fp["code"] == "s005"]
        self.assertTrue(
            any("korekcia" in fp["name"] for fp in korekcia),
            "and it must say WHICH column, because brutto and korekcia are "
            "different things on the filed form: %s"
            % [fp["name"] for fp in korekcia])

    def test_a_base_account_still_reports_its_own_row(self):
        """The control: 013000 feeds r005's brutto and is not mislabelled."""
        move = self._post("013000", "321000")
        line = move.line_ids.filtered(
            lambda l: l.account_id.code == "013000")
        rows = [fp for fp in line._cssk_statutory_footprint()
                if fp["code"] == "s005"]
        self.assertTrue(rows, "013000 feeds r005")
        self.assertFalse(any("korekcia" in fp["name"] for fp in rows),
                         "and it is the BRUTTO side")

    def test_the_footprint_honours_the_claimed_set(self):
        """It must not over-report a residual the evaluator would never absorb.

        The footprint used to reduce every token to its digits, so a residual
        ``NNX`` became the bare prefix ``NN`` and claimed every account of the
        group — including ones another row names outright. Driving it through
        the same matcher the statement computes with is what fixes it, and
        this asserts the two now agree about one account.
        """
        version = self.env.ref("l10n_sk_fs.uzpod_v14")
        claimed = version._cssk_claimed_codes()
        self.assertIsNotNone(claimed, "UZPODv14 absorbs analytics")
        matcher = self.env["cssk.fs.statement"]
        # 311110 is routed to a row of its own, so the 311000 main token must
        # NOT absorb it — forward and reverse must give the same answer.
        self.assertFalse(
            matcher._cssk_code_matches("311110", "311000", claimed),
            "an explicitly-routed analytic is not absorbed by its main")
        move = self._post("311110", "602000")
        line = move.line_ids.filtered(
            lambda l: l.account_id.code == "311110")
        codes = {fp["code"] for fp in line._cssk_statutory_footprint()}
        self.assertIn("s043", codes, "311110 is r043's own analytic")

    def test_a_tagged_account_reports_ONE_row_not_the_whole_family(self):
        """Úč POD 2 splits IX/X/XI/N by account TAG, and so must the drill.

        `665&IX_1`, `665&IX_2` and `665!IX_1!IX_2` share one account code and
        differ only by tag, so reducing a token to its digits reported a
        posting on a 665 account as feeding all three — including the residual
        "ostatné" leaf it definitively does not reach.

        Unlike a two-sided account, a single posting DOES decide this: the tag
        is on the account. The information is there, so the answer should use
        it.
        """
        tag = self.env.ref("l10n_sk_fs.account_tag_pl_IX_1",
                           raise_if_not_found=False)
        if not tag:
            self.skipTest("the IX_1 split tag is not installed")
        account = self.env["account.account"].with_company(self.company).create({
            "name": "Výnosy z CP — prepojené", "code": "665100",
            "account_type": "income",
            "company_ids": [(6, 0, [self.company.id])],
            "tag_ids": [(6, 0, tag.ids)],
        })
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": account.id, "credit": 700.0}),
                (0, 0, {"account_id": self._account("221000").id,
                        "debit": 700.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered(lambda l: l.account_id == account)
        codes = {fp["code"] for fp in line._cssk_statutory_footprint()}
        self.assertIn("v32", codes, "IX.1 is the row this account feeds")
        self.assertNotIn("v33", codes, "IX.2 is a different tag")
        self.assertNotIn(
            "v34", codes,
            "and the residual 'ostatné' leaf EXCLUDES a tagged account")

    def test_an_untagged_account_reaches_the_ostatne_leaf(self):
        """The other side of the same filter: `665!IX_1!IX_2`.

        An account of the family carrying neither tag is exactly what the
        residual leaf is for, and it must not be reported against the two
        tagged rows.
        """
        if not self.env.ref("l10n_sk_fs.account_tag_pl_IX_1",
                            raise_if_not_found=False):
            self.skipTest("the IX split tags are not installed")
        account = self.env["account.account"].with_company(self.company).create({
            "name": "Výnosy z CP — ostatné", "code": "665900",
            "account_type": "income",
            "company_ids": [(6, 0, [self.company.id])],
        })
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": account.id, "credit": 300.0}),
                (0, 0, {"account_id": self._account("221000").id,
                        "debit": 300.0}),
            ],
        })
        move.action_post()
        line = move.line_ids.filtered(lambda l: l.account_id == account)
        codes = {fp["code"] for fp in line._cssk_statutory_footprint()}
        self.assertIn("v34", codes, "untagged is what 'ostatné' means")
        self.assertNotIn("v32", codes)
        self.assertNotIn("v33", codes)
