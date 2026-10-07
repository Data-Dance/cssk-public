# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPDP9 výkazy (VetaUA / VetaUB / VetaUD) from the l10n_cz_fs statements.

Three questions, three tests, because each check is blind to what the others
catch (a balanced sheet proves none of them):

* is every row of the zkrácený rozsah mapped or declared not applicable —
  a silent unmapped row files as zero and nothing anywhere complains;
* does each EPO total equal the sum of its statutory parts by SIGNED WEIGHT
  per account — the only comparison that sees an account claimed by two
  sibling rows, or an aggregate missing a term, under a sheet that still foots;
* does a real ledger come out on the right rows, in the right columns,
  XSD-valid.

The matcher and the formula parser are duplicated here on purpose: a test that
validates row DATA must not run through the code whose behaviour it checks.
"""

import base64
import csv
import hashlib
import os
import re
from collections import Counter

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools.misc import file_path

from odoo.addons.l10n_cz_dppo.models import dppdp9_vykazy as vykazy

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XS = "{http://www.w3.org/2001/XMLSchema}"

#: The statutory arithmetic of the výkazy (vyhláška 500/2002 Sb., přílohy 1
#: and 2), written from the form, NOT from the l10n_cz_fs aggregate formulas —
#: those are what is being checked. {věta: {total row: [± part rows]}}.
IDENTITIES = {
    "UA": {1: [2, 3, 37, 74], 3: [4, 14, 27], 37: [38, 46, 68, 71],
           46: [47, 57, 78]},
    "UD": {1: [2, 24, 64], 2: [3, 7, 15, 18, 22, 23], 24: [25, 30],
           30: [31, 46, 67]},
    "UB": {30: [1, 2, -3, -7, -8, -9, -14, 20, -24],
           48: [31, -34, 35, -38, 39, -42, -43, 46, -47],
           49: [30, 48], 53: [49, -50], 55: [53, -54],
           56: [1, 2, 20, 31, 35, 39, 46]},
}

#: Rows whose l10n_cz_fs designation legitimately differs from the číselník's.
#: C.II.2. is filed from C.II. because the chart convention makes every
#: receivable krátkodobé — NOT_APPLICABLE[("UA", 47)] states why.
DESIGNATION_CONVENTIONS = {("UA", 57)}


def _norm(designation):
    return (designation or "").strip().rstrip(".")


def _load_ciselnik():
    with open(os.path.join(MODULE_DIR, "data", "uv_radky_500.csv"),
              encoding="utf-8") as fh:
        return {(r["veta"], int(r["c_radku"])): r for r in csv.DictReader(fh)}


@tagged("post_install", "-at_install")
class TestCzDppoVykazy(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env[
            "cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")],
            limit=1)
        cls.version = cls.env.ref("l10n_cz_dppo.cz_dppo_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_dppo.cz_dppo_type_B")
        cls.bs_version = cls.env.ref("l10n_cz_fs.rozvaha_version_2025")
        cls.pl_version = cls.env.ref("l10n_cz_fs.vysledovka_version_2025")
        cls.misc = cls.company_data["default_journal_misc"]
        cls.ciselnik = _load_ciselnik()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _acc(self, like):
        acc = self.env["account.account"].search(
            [("code", "=like", like), ("company_ids", "in", self.company.id)],
            limit=1)
        self.assertTrue(acc, "the CZ chart has no %s account" % like)
        return acc

    def _post(self, date, lines):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.misc.id, "date": date,
            "line_ids": [Command.create({"account_id": self._acc(a).id,
                                         "debit": d, "credit": c})
                         for a, d, c in lines]})
        move.action_post()

    def _statement(self, version):
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        st.action_compute_lines()
        return st

    def _return(self, **vals):
        ret = self.env["cssk.income.tax.return"].create(dict({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"}, **vals))
        ret.action_compute_lines()
        return ret

    def _chart_codes(self):
        """The l10n_cz chart as SHIPPED, off-balance accounts aside.

        Not the test company's accounts: the invoicing test fixture copies
        accounts to make its own (343221 → 343222), and a mapping is judged
        against the chart, not against a fixture's artefacts. Accounts a
        customer adds are the runtime unmapped diagnostic's job."""
        with open(file_path("l10n_cz/data/template/account.account-cz.csv"),
                  encoding="utf-8") as fh:
            return [r["code"] for r in csv.DictReader(fh)
                    if r["account_type"] != "off_balance"]

    def _fs_weights(self, version, codes):
        """{fs row code: Counter(account code -> signed weight)}."""
        defs = {d.code: d for d in version.line_def_ids}
        cache = {}

        def leaf(ldef):
            w = Counter()
            # netto = gross + the (credit) correction balances: both columns
            # carry their tokens' own sign into the reported figure.
            for formula in (ldef.account_formula,
                            ldef.account_formula_correction):
                for tok in (formula or "").split(","):
                    tok = tok.strip()
                    if not tok:
                        continue
                    sign = -1 if tok.startswith("-") else 1
                    prefix = tok.lstrip("-")
                    self.assertTrue(prefix.isdigit(), "token %r" % tok)
                    for code in codes:
                        if code.startswith(prefix):
                            w[code] += sign
            return w

        def weight(code):
            if code in cache:
                return cache[code]
            ldef = defs[code]
            if ldef.kind == "aggregate":
                formula = ldef.aggregate_formula or ""
                self.assertRegex(
                    formula,
                    r"^\s*[A-Za-z_]\w*(\s*[+-]\s*[A-Za-z_]\w*)*\s*$",
                    "%s: only a signed sum can be compared by weight" % code)
                w = Counter()
                for sign, ref in re.findall(r"([+-]?)\s*([A-Za-z_]\w*)",
                                            formula):
                    for acc, n in weight(ref).items():
                        w[acc] += -n if sign == "-" else n
            else:
                w = leaf(ldef)
            cache[code] = w
            return w

        return {code: weight(code) for code in defs}

    def _row_weights(self):
        codes = self._chart_codes()
        fs = {"balance_sheet": self._fs_weights(self.bs_version, codes),
              "profit_loss": self._fs_weights(self.pl_version, codes)}
        rows = {}
        for (veta, row), (_d, fs_codes) in vykazy.ROWS.items():
            w = Counter()
            for code in fs_codes:
                w.update(fs[vykazy.TABLES[veta]][code])
            rows[(veta, row)] = w
        return rows

    @staticmethod
    def _clean(counter):
        return {k: v for k, v in counter.items() if v}

    # ------------------------------------------------------------------
    # 1. every row is accounted for
    # ------------------------------------------------------------------
    def test_every_vykaz_row_is_mapped_or_declared(self):
        # Every výkaz record the XSD defines (a VetaU* element with a
        # c_radku) is either filed or declared not applicable, table by
        # table. VetaR also has a c_radku, but it is the II. oddíl's own
        # row-by-row příloha (t_prilohy / kod_sekce), not an účetní výkaz.
        xsd = etree.parse(os.path.join(MODULE_DIR, "data", "dppdp9_epo2.xsd"))
        tables = {
            el.get("name")[len("Veta"):]
            for el in xsd.iter(XS + "element")
            if (el.get("name") or "").startswith("VetaU")
            and el.find("%scomplexType/%sattribute[@name='c_radku']"
                        % (XS, XS)) is not None
        }
        self.assertTrue(tables, "premise: the XSD defines výkaz records")
        self.assertEqual(
            tables, set(vykazy.TABLES) | set(vykazy.NOT_APPLICABLE_TABLES),
            "a výkaz record of the XSD is neither filed nor declared")
        self.assertFalse(set(vykazy.TABLES) & set(vykazy.NOT_APPLICABLE_TABLES))

        # Within the filed tables, every row of the filed rozsah is mapped or
        # declared, never both, and nothing outside the rozsah is filed.
        in_range = {key for key, r in self.ciselnik.items()
                    if vykazy.RANGE in r["rozsah"]}
        self.assertEqual({veta for veta, _row in self.ciselnik},
                         set(vykazy.TABLES))
        mapped, declared = set(vykazy.ROWS), set(vykazy.NOT_APPLICABLE)
        self.assertFalse(mapped & declared, "a row is both mapped and n/a")
        silent = in_range - mapped - declared
        self.assertFalse(silent, "zkrácený-rozsah rows filed as a silent zero: "
                                 "%s" % sorted(silent))
        self.assertFalse((mapped | declared) - in_range,
                         "rows outside the zkrácený rozsah (or outside the "
                         "číselník altogether) are mapped")
        for key, reason in vykazy.NOT_APPLICABLE.items():
            self.assertGreater(len(reason), 40, "%s needs a real reason" % (key,))

        # Mapping is by statutory designation: the číselník's and the
        # l10n_cz_fs row's must agree, so a row number typed wrong shows.
        names = {
            kind: {d.code: d.name for d in version.line_def_ids}
            for kind, version in (("balance_sheet", self.bs_version),
                                  ("profit_loss", self.pl_version))}
        for (veta, row), (designation, codes) in vykazy.ROWS.items():
            official = self.ciselnik[(veta, row)]["oznaceni"]
            self.assertEqual(_norm(designation), _norm(official),
                             "%s/%s: designation" % (veta, row))
            for code in codes:
                self.assertIn(code, names[vykazy.TABLES[veta]],
                              "%s/%s: l10n_cz_fs has no row %s"
                              % (veta, row, code))
            if len(codes) != 1 or (veta, row) in DESIGNATION_CONVENTIONS:
                continue
            first = names[vykazy.TABLES[veta]][codes[0]].split()[0]
            fs_designation = first if ("." in first or set(first) == {"*"}) \
                else ""
            self.assertEqual(_norm(fs_designation), _norm(official),
                             "%s/%s is filed from l10n_cz_fs %s (%s)"
                             % (veta, row, codes[0], first))

    # ------------------------------------------------------------------
    # 2. the statute's arithmetic, by signed weight per account
    # ------------------------------------------------------------------
    def test_statutory_totals_hold_by_signed_weight(self):
        rows = self._row_weights()

        def w(veta, row):
            return rows.get((veta, row), Counter())   # n/a rows weigh nothing

        for veta, identities in IDENTITIES.items():
            for total, parts in identities.items():
                expected = Counter()
                for part in parts:
                    for acc, n in w(veta, abs(part)).items():
                        expected[acc] += n if part > 0 else -n
                self.assertEqual(
                    self._clean(w(veta, total)), self._clean(expected),
                    "%s row %s is not the sum of %s" % (veta, total, parts))

    def test_each_account_lands_on_one_leaf_row(self):
        rows = self._row_weights()
        for veta, identities in IDENTITIES.items():
            leaves = [key for key in rows
                      if key[0] == veta and key[1] not in identities]
            reach = Counter()
            for key in leaves:
                for acc, n in rows[key].items():
                    reach[acc] += abs(n)
            doubled = {acc: n for acc, n in reach.items() if n > 1}
            self.assertFalse(doubled, "%s: accounts on two leaf rows: %s"
                             % (veta, doubled))

    def test_every_account_reaches_the_zaverka(self):
        rows = self._row_weights()
        aktiva, pasiva = rows[("UA", 1)], rows[("UD", 1)]
        missing = [code for code in self._chart_codes()
                   if code[:1] in "01234"
                   and abs(aktiva[code]) + abs(pasiva[code]) != 1]
        self.assertFalse(missing, "balance-sheet accounts on neither or both "
                                  "sides: %s" % missing)
        # A.V of the Rozvaha and *** of the VZZ are one number: every class
        # 5/6 account carries the same weight in both.
        result_bs, result_pl = rows[("UD", 22)], rows[("UB", 55)]
        drift = {code: (result_bs[code], result_pl[code])
                 for code in self._chart_codes()
                 if code[:1] in "56" and result_bs[code] != result_pl[code]}
        self.assertFalse(drift, "A.V and VH za účetní období disagree on "
                                "(A.V weight, *** weight): %s" % drift)

    # ------------------------------------------------------------------
    # 3. a real ledger, exported
    # ------------------------------------------------------------------
    def _ledger(self):
        self._post("2024-06-30", [("221%", 50000.0, 0.0),
                                  ("411%", 0.0, 50000.0)])
        self._post("2025-01-10", [("221%", 1000000.0, 0.0),
                                  ("411%", 0.0, 1000000.0)])
        self._post("2025-02-01", [("022%", 600000.0, 0.0),
                                  ("221%", 0.0, 600000.0)])
        self._post("2025-12-31", [("551%", 120000.0, 0.0),
                                  ("082%", 0.0, 120000.0)])
        self._post("2025-06-30", [("311%", 500000.0, 0.0),
                                  ("602%", 0.0, 500000.0)])
        self._post("2025-12-31", [("558%", 20000.0, 0.0),
                                  ("391%", 0.0, 20000.0)])
        self._post("2025-03-31", [("501%", 100000.0, 0.0),
                                  ("321%", 0.0, 100000.0)])

    def _rows_of(self, root, veta):
        return {int(el.get("c_radku")): dict(el.attrib)
                for el in root.iter("Veta" + veta)}

    def test_export_files_the_vykazy(self):
        self._ledger()
        self.company.partner_id.nace_code = "62101"
        bs = self._statement(self.bs_version)
        pl = self._statement(self.pl_version)
        ret = self._return(l10n_cz_fs_balance_sheet_id=bs.id,
                           l10n_cz_fs_profit_loss_id=pl.id)
        ret.action_export_xml()     # validates against the bundled XSD
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

        head = root.find(".//VetaD")
        # c_nace: EPO's critical check wants an existing CZ-NACE code.
        self.assertEqual(head.get("c_nace"), "62101")
        self.assertEqual(head.get("uv_vyhl"), "500")
        self.assertEqual(head.get("uv_rozsah"), "Z")
        self.assertEqual(head.get("uv_mena"), "CZK")
        self.assertEqual(head.get("uz_rad"), "T")
        self.assertEqual(head.get("d_uv"), "31.12.2025")

        ua, ud, ub = (self._rows_of(root, v) for v in ("UA", "UD", "UB"))
        # B.II.: 022 600 000 less oprávky 082 120 000, in thousands
        self.assertEqual(ua[14], {"c_radku": "14", "kc_brutto": "600",
                                  "kc_korekce": "120", "kc_netto": "480"})
        # C.II. and C.II.2.: 311 500 000 less OP 391 20 000
        for row in (46, 57):
            self.assertEqual(ua[row]["kc_netto"], "480")
            self.assertEqual(ua[row]["kc_korekce"], "20")
        self.assertNotIn(47, ua, "C.II.1. is declared n/a, never filed")
        # C.IV.: 50 000 (2024) + 1 000 000 − 600 000; prior year 50 000
        self.assertEqual(ua[71], {"c_radku": "71", "kc_brutto": "450",
                                  "kc_netto": "450", "kc_netto_min": "50"})
        self.assertEqual(ua[1]["kc_brutto"], "1550")
        self.assertEqual(ua[1]["kc_korekce"], "140")
        self.assertEqual(ua[1]["kc_netto"], "1410")
        # pasiva
        self.assertEqual(ud[1], {"c_radku": "1", "kc_sled": "1410",
                                 "kc_min": "50"})
        self.assertEqual(ud[3]["kc_sled"], "1050")
        self.assertEqual(ud[22]["kc_sled"], "260")     # A.V
        self.assertEqual(ud[24]["kc_sled"], "100")     # B.+C.
        self.assertEqual(ud[46]["kc_sled"], "100")     # C.II. (321)
        # VZZ
        self.assertEqual(ub[1]["kc_sled"], "500")
        self.assertEqual(ub[3]["kc_sled"], "100")
        self.assertEqual(ub[14]["kc_sled"], "140")     # E. (551 + 558)
        self.assertEqual(ub[30]["kc_sled"], "260")
        self.assertEqual(ub[55]["kc_sled"], "260")     # = A.V
        self.assertEqual(ub[56]["kc_sled"], "500")
        # The XSD's sequence puts the výkazy after VetaO, UA before UB before UD.
        order = [etree.QName(el).localname for el in root.find("DPPDP9")]
        self.assertEqual(order[:3], ["VetaD", "VetaP", "VetaO"])
        self.assertEqual(order.index("VetaUB"), order.index("VetaUA") + len(ua))

    def test_export_without_statements_says_so(self):
        ret = self._return()
        ret.action_export_xml()
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertIsNone(root.find(".//VetaUA"))
        self.assertIsNone(root.find(".//VetaD").get("uv_rozsah"))
        self.assertIn("E-příloha", ret.message_ids[:1].body)

    def test_a_wrong_link_is_refused_not_filed(self):
        pl = self._statement(self.pl_version)
        bs = self._statement(self.bs_version)
        with self.assertRaisesRegex(UserError, "or neither"):
            self._return(l10n_cz_fs_profit_loss_id=pl.id).action_export_xml()
        other = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.pl_version.id,
            "date_from": "2025-07-01", "date_to": "2025-12-31"})
        other.action_compute_lines()
        with self.assertRaisesRegex(UserError, "zdaňovací období"):
            self._return(l10n_cz_fs_balance_sheet_id=bs.id,
                         l10n_cz_fs_profit_loss_id=other.id).action_export_xml()
        draft = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.bs_version.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        with self.assertRaisesRegex(UserError, "not been computed"):
            self._return(l10n_cz_fs_balance_sheet_id=draft.id,
                         l10n_cz_fs_profit_loss_id=pl.id).action_export_xml()
        # A statement of another version lacks the rows the výkaz reads.
        bs.line_ids.filtered(lambda ln: ln.code == "CIV").unlink()
        with self.assertRaisesRegex(UserError, "CIV"):
            self._return(l10n_cz_fs_balance_sheet_id=bs.id,
                         l10n_cz_fs_profit_loss_id=pl.id).action_export_xml()

    def test_linked_but_empty_is_still_a_filed_zaverka(self):
        """A linked závěrka whose every row rounds to nothing still carries
        the výkaz header — it must not read as "no závěrka filed"."""
        ret = self._return(
            l10n_cz_fs_balance_sheet_id=self._statement(self.bs_version).id,
            l10n_cz_fs_profit_loss_id=self._statement(self.pl_version).id)
        ret.action_export_xml()
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(root.find(".//VetaD").get("uv_rozsah"), "Z")
        self.assertIsNone(root.find(".//VetaUA"))

    def test_negative_korekce_is_refused(self):
        """kc_korekce is filed unsigned. A debit balance on an oprávka is a
        booking error to fix, not a sign to drop silently."""
        self._post("2025-05-31", [("082%", 5000.0, 0.0),
                                  ("221%", 0.0, 5000.0)])
        ret = self._return(
            l10n_cz_fs_balance_sheet_id=self._statement(self.bs_version).id,
            l10n_cz_fs_profit_loss_id=self._statement(self.pl_version).id)
        with self.assertRaisesRegex(UserError, "negative korekce"):
            ret.action_export_xml()

    # ------------------------------------------------------------------
    # 4. the pin
    # ------------------------------------------------------------------
    def test_schema_and_ciselnik_are_pinned(self):
        with open(os.path.join(MODULE_DIR, "data", "SCHEMA_VERSION"),
                  encoding="utf-8") as fh:
            pin = fh.read()
        verze = pin.split()[1]
        for name in ("dppdp9_epo2.xsd", "uv_radky_500.csv"):
            m = re.search(r"^%s\s+(\d+)\s+([0-9a-f]{32})$" % re.escape(name),
                          pin, re.M)
            self.assertTrue(m, "%s is not pinned" % name)
            with open(os.path.join(MODULE_DIR, "data", name), "rb") as fh:
                data = fh.read()
            self.assertEqual((len(data), hashlib.md5(data).hexdigest()),
                             (int(m.group(1)), m.group(2)),
                             "%s changed without its pin" % name)
        with open(os.path.join(MODULE_DIR, "report", "dppo_report.xml"),
                  encoding="utf-8") as fh:
            self.assertIn('verzePis="%s"' % verze, fh.read())
