# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPDP9 výkazy (VetaUA / VetaUB / VetaUD) from the l10n_cz_fs statements.

Three questions, three tests, because each check is blind to what the others
catch (a balanced sheet proves none of them):

* is every row of the filed rozsah (plný and zkrácený alike) mapped or
  declared not applicable —
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

def _parent(designation):
    """``B.I.2.1.`` -> ``B.I.2``; None for a top-level item."""
    parts = _norm(designation).replace(" ", "").split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else None


def _identities_full(ciselnik):
    """The plný rozsah's arithmetic: the top-level identities above, plus
    every numbered item = the sum of the items one level below it, read off
    the číselník's own designations (B.I.2. = B.I.2.1. + B.I.2.2.)."""
    out = {veta: {total: list(parts) for total, parts in ids.items()}
           for veta, ids in IDENTITIES.items()}
    for veta in IDENTITIES:
        rows = {key[1]: r for key, r in ciselnik.items()
                if key[0] == veta and "P" in r["rozsah"]}
        by_designation = {}
        for row, r in rows.items():
            by_designation.setdefault(_norm(r["oznaceni"]).replace(" ", ""),
                                      []).append(row)
        children = {}
        for row, r in sorted(rows.items()):
            # "B.+C." is a sum of two letters, not an item below "B."
            parent = None if "+" in r["oznaceni"] else _parent(r["oznaceni"])
            if not parent or parent not in by_designation:
                continue
            (total,) = by_designation[parent]
            children.setdefault(total, []).append(row)
        for total, parts in children.items():
            if total in out[veta]:
                # the top-level identity already says it — and must agree
                assert set(parts) <= set(out[veta][total]), (veta, total)
                continue
            out[veta][total] = parts
    return out


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
        cls.bs_full = cls.env.ref("l10n_cz_fs.rozvaha_full_version_2025")
        cls.pl_full = cls.env.ref("l10n_cz_fs.vysledovka_full_version_2025")
        cls.versions = {
            vykazy.ABRIDGED: {"balance_sheet": cls.bs_version,
                              "profit_loss": cls.pl_version},
            vykazy.FULL: {"balance_sheet": cls.bs_full,
                          "profit_loss": cls.pl_full},
        }
        cls.misc = cls.company_data["default_journal_misc"]
        cls.ciselnik = _load_ciselnik()
        cls.identities = {vykazy.ABRIDGED: IDENTITIES,
                          vykazy.FULL: _identities_full(cls.ciselnik)}

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
                    body = tok.lstrip("-")
                    # On the chart as shipped nothing is tagged: "&TAG"
                    # (tagged accounts only) weighs nothing, "!TAG"
                    # (everything not tagged) weighs the whole prefix.
                    if "&" in body:
                        continue
                    prefix = body.split("!")[0]
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

    def _row_weights(self, rng):
        codes = self._chart_codes()
        fs = {kind: self._fs_weights(version, codes)
              for kind, version in self.versions[rng].items()}
        rows = {}
        for (veta, row), (_d, fs_codes) in vykazy.rows(rng).items():
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

        self.assertEqual({veta for veta, _row in self.ciselnik},
                         set(vykazy.TABLES))
        for rng in vykazy.RANGES:
            self._check_rozsah_is_mapped(rng)

    def _check_rozsah_is_mapped(self, rng):
        # Within the filed tables, every row of the filed rozsah is mapped or
        # declared, never both, and nothing outside the rozsah is filed.
        in_range = {key for key, r in self.ciselnik.items()
                    if rng in r["rozsah"]}
        row_map, na = vykazy.rows(rng), vykazy.not_applicable(rng)
        mapped, declared = set(row_map), set(na)
        self.assertFalse(mapped & declared, "%s: a row is both mapped and "
                                            "n/a" % rng)
        silent = in_range - mapped - declared
        self.assertFalse(silent, "%s-rozsah rows filed as a silent zero: "
                                 "%s" % (rng, sorted(silent)))
        self.assertFalse((mapped | declared) - in_range,
                         "rows outside the %s rozsah (or outside the "
                         "číselník altogether) are mapped" % rng)
        for key, reason in na.items():
            self.assertGreater(len(reason), 40, "%s needs a real reason" % (key,))

        # Mapping is by statutory designation: the číselník's and the
        # l10n_cz_fs row's must agree, so a row number typed wrong shows.
        names = {
            kind: {d.code: d.name for d in version.line_def_ids}
            for kind, version in self.versions[rng].items()}
        conventions = DESIGNATION_CONVENTIONS if rng == vykazy.ABRIDGED \
            else set()
        for (veta, row), (designation, codes) in row_map.items():
            official = self.ciselnik[(veta, row)]["oznaceni"]
            self.assertEqual(_norm(designation), _norm(official),
                             "%s %s/%s: designation" % (rng, veta, row))
            for code in codes:
                self.assertIn(code, names[vykazy.TABLES[veta]],
                              "%s %s/%s: l10n_cz_fs has no row %s"
                              % (rng, veta, row, code))
            if len(codes) != 1 or (veta, row) in conventions:
                continue
            first = names[vykazy.TABLES[veta]][codes[0]].split()[0]
            fs_designation = first if ("." in first or set(first) == {"*"}) \
                else ""
            self.assertEqual(
                _norm(fs_designation).replace(" ", ""),
                _norm(official).replace(" ", ""),
                "%s %s/%s is filed from l10n_cz_fs %s (%s)"
                % (rng, veta, row, codes[0], first))
        if rng == vykazy.FULL:
            # The plný rozsah files every row of its versions: a row the
            # version shows and the return never files would be a figure the
            # accountant sees and the Finanční správa does not.
            for kind, version in self.versions[rng].items():
                filed = vykazy.fs_codes(kind, rng)
                self.assertEqual(
                    set(version.line_def_ids.mapped("code")) - filed, set(),
                    "%s rows the DPPDP9 never files" % version.name)

    # ------------------------------------------------------------------
    # 2. the statute's arithmetic, by signed weight per account
    # ------------------------------------------------------------------
    def test_statutory_totals_hold_by_signed_weight(self):
        for rng in vykazy.RANGES:
            rows = self._row_weights(rng)

            def w(veta, row):
                return rows.get((veta, row), Counter())   # n/a rows: nothing

            for veta, identities in self.identities[rng].items():
                for total, parts in identities.items():
                    expected = Counter()
                    for part in parts:
                        for acc, n in w(veta, abs(part)).items():
                            expected[acc] += n if part > 0 else -n
                    self.assertEqual(
                        self._clean(w(veta, total)), self._clean(expected),
                        "%s: %s row %s is not the sum of %s"
                        % (rng, veta, total, parts))

    def test_each_account_lands_on_one_leaf_row(self):
        for rng in vykazy.RANGES:
            rows = self._row_weights(rng)
            for veta, identities in self.identities[rng].items():
                leaves = [key for key in rows
                          if key[0] == veta and key[1] not in identities]
                reach = Counter()
                for key in leaves:
                    for acc, n in rows[key].items():
                        reach[acc] += abs(n)
                doubled = {acc: n for acc, n in reach.items() if n > 1}
                self.assertFalse(doubled, "%s %s: accounts on two leaf rows: "
                                          "%s" % (rng, veta, doubled))

    def test_every_account_reaches_the_zaverka(self):
        for rng in vykazy.RANGES:
            rows = self._row_weights(rng)
            # An account the version names on BOTH sides is reported by the
            # sign of its own balance (221 in funds or overdrawn, 481 a
            # pohledávka or a závazek): +1 on the aktiva, -1 on the pasiva.
            two_sided = self.versions[rng][
                "balance_sheet"]._cssk_two_sided_prefixes()
            aktiva, pasiva = rows[("UA", 1)], rows[("UD", 1)]
            wrong = []
            for code in self._chart_codes():
                if code[:1] not in "01234":
                    continue
                if any(code.startswith(p) for p in two_sided):
                    if (aktiva[code], pasiva[code]) != (1, -1):
                        wrong.append(code)
                elif abs(aktiva[code]) + abs(pasiva[code]) != 1:
                    wrong.append(code)
            self.assertFalse(wrong, "%s: balance-sheet accounts on neither or "
                                    "both sides: %s" % (rng, wrong))
            # A.V of the Rozvaha and *** of the VZZ are one number: every
            # class 5/6 account carries the same weight in both.
            result_bs, result_pl = rows[("UD", 22)], rows[("UB", 55)]
            drift = {code: (result_bs[code], result_pl[code])
                     for code in self._chart_codes()
                     if code[:1] in "56" and result_bs[code] != result_pl[code]}
            self.assertFalse(drift, "%s: A.V and VH za účetní období disagree "
                                    "on (A.V weight, *** weight): %s"
                                    % (rng, drift))

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

    def test_export_files_the_full_vykazy(self):
        """The plný rozsah: uv_rozsah P, the numbered rows filed, the korekce
        on the row its brutto sits on, and every total still the sum of its
        parts as filed."""
        self._ledger()
        self.company.partner_id.nace_code = "62101"
        bs, pl = self._statement(self.bs_full), self._statement(self.pl_full)
        ret = self._return(l10n_cz_fs_balance_sheet_id=bs.id,
                           l10n_cz_fs_profit_loss_id=pl.id)
        ret.action_export_xml()     # validates against the bundled XSD
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(root.find(".//VetaD").get("uv_rozsah"), "P")
        ua, ud, ub = (self._rows_of(root, v) for v in ("UA", "UD", "UB"))
        # B.II. and B.II.2. Hmotné movité věci: 022 600 000 less 082 120 000
        for row in (14, 18):
            self.assertEqual(
                {k: v for k, v in ua[row].items() if k != "c_radku"},
                {"kc_brutto": "600", "kc_korekce": "120", "kc_netto": "480"})
        # C.II.2.1. Pohledávky z obchodních vztahů: 311 less OP 391
        self.assertEqual(ua[58]["kc_netto"], "480")
        self.assertEqual(ua[58]["kc_korekce"], "20")
        self.assertEqual(ua[57]["kc_netto"], "480")    # C.II.2.
        self.assertNotIn(47, ua, "nothing long-term, nothing filed")
        self.assertEqual(ua[73]["kc_netto"], "450")    # C.IV.2. na účtech
        self.assertEqual(ua[1]["kc_netto"], "1410")
        self.assertEqual(ud[4]["kc_sled"], "1050")     # A.I.1.
        self.assertEqual(ud[52]["kc_sled"], "100")     # C.II.4. (321)
        self.assertEqual(ud[1]["kc_sled"], "1410")
        self.assertEqual(ub[5]["kc_sled"], "100")      # A.2. (501)
        self.assertEqual(ub[16]["kc_sled"], "120")     # E.1.1. odpisy
        self.assertEqual(ub[19]["kc_sled"], "20")      # E.3. OP k pohledávkám
        self.assertEqual(ub[14]["kc_sled"], "140")     # E.
        self.assertEqual(ub[55]["kc_sled"], "260")
        for veta, rows in (("UA", ua), ("UD", ud), ("UB", ub)):
            column = "kc_netto" if veta == "UA" else "kc_sled"
            for total, parts in self.identities[vykazy.FULL][veta].items():
                value = int(rows.get(total, {}).get(column, 0))
                parts_sum = sum(
                    (1 if p > 0 else -1)
                    * int(rows.get(abs(p), {}).get(column, 0))
                    for p in parts)
                # Rounding to thousands is per row; the ledger is chosen so
                # no row rounds.
                self.assertEqual(value, parts_sum, "%s %s" % (veta, total))

    def test_mixed_rozsah_is_refused(self):
        """uv_rozsah covers both výkazy: a plný VZZ beside a zkrácený
        Rozvaha cannot be filed as either without misstating one of them."""
        ret = self._return(
            l10n_cz_fs_balance_sheet_id=self._statement(self.bs_version).id,
            l10n_cz_fs_profit_loss_id=self._statement(self.pl_full).id)
        with self.assertRaisesRegex(UserError, "different rozsahy"):
            ret.action_export_xml()

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
