# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The plný rozsah (vyhláška 500/2002 Sb., § 3a odst. 1 and 3).

Four questions, each blind to the others:

* does every item the zkrácený rozsah shares with the plný one cover the same
  accounts in both — the two are separate row sets and could drift apart;
* does a real ledger come out on the right numbered rows, including the rows
  read by account tag and the accounts reported by the sign of their balance;
* does New land on the plný rozsah, and can an account carry two split tags;
* does the upgrade name the existing versions without touching an edit.

The account matcher is re-implemented here on purpose: a test that validates
row DATA must not run through the code whose behaviour it checks.
"""

import base64
import csv
import importlib.util
import re
from collections import Counter

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools.misc import file_path

#: Accounts on which the plný rozsah DELIBERATELY differs from the zkrácený
#: one, and why. Everything else must weigh the same under every shared code.
FULL_VS_ABRIDGED = {
    # Reported by the sign of the account's own balance (both sides named):
    "221": "an overdrawn bank account is C.II.2 Závazky k úvěrovým "
           "institucím (§ 12a odst. 2)",
    "336": "a debit balance is C.II.2.4.2",
    "341": "a debit balance is C.II.2.4.3 Stát - daňové pohledávky",
    "342": "idem",
    "343000": "idem",
    "345": "idem",
    "346": "idem",
    "347": "idem",
    "373": "a credit balance is C.II.8.7 Jiné závazky",
    "481": "a debit balance is C.II.1.4 Odložená daňová pohledávka",
    # Placed by the vyhláška, where the zkrácený version predates the check:
    "491": "A.I.1 (§ 14 odst. 1), not A.IV",
}


def _weights(version, chart_codes):
    """{row code: Counter(account -> signed weight)} on an UNTAGGED chart.

    ``665&IV_1`` (tagged accounts only) weighs nothing on the chart as
    shipped; ``665!IV_1`` (everything not tagged) weighs the whole prefix."""
    defs = {d.code: d for d in version.line_def_ids}
    cache = {}

    def leaf(ldef):
        w = Counter()
        for formula in (ldef.account_formula, ldef.account_formula_correction):
            for tok in (formula or "").split(","):
                tok = tok.strip()
                if not tok:
                    continue
                sign = -1 if tok.startswith("-") else 1
                body = tok.lstrip("-")
                if "&" in body:
                    continue
                prefix = re.split(r"[!]", body)[0]
                assert prefix.isdigit(), tok
                for code in chart_codes:
                    if code.startswith(prefix):
                        w[code] += sign
        return w

    def weight(code):
        if code not in cache:
            ldef = defs[code]
            if ldef.kind == "aggregate":
                w = Counter()
                for sign, ref in re.findall(r"([+-]?)\s*([A-Za-z_]\w*)",
                                            ldef.aggregate_formula or ""):
                    for acc, n in weight(ref).items():
                        w[acc] += -n if sign == "-" else n
            else:
                w = leaf(ldef)
            cache[code] = w
        return cache[code]

    return {code: weight(code) for code in defs}


@tagged("post_install", "-at_install")
class TestCzFsFull(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
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
        cls.bs_full = cls.env.ref("l10n_cz_fs.rozvaha_full_version_2025")
        cls.pl_full = cls.env.ref("l10n_cz_fs.vysledovka_full_version_2025")
        cls.bs_abr = cls.env.ref("l10n_cz_fs.rozvaha_version_2025")
        cls.pl_abr = cls.env.ref("l10n_cz_fs.vysledovka_version_2025")
        cls.misc = cls.company_data["default_journal_misc"]

    # ------------------------------------------------------------------
    def _acc(self, like):
        acc = self.env["account.account"].search(
            [("code", "=like", like), ("company_ids", "in", self.company.id)],
            limit=1)
        self.assertTrue(acc, "no %s account" % like)
        return acc

    def _new_acc(self, code, name, account_type, tag=None):
        vals = {"name": name, "code": code, "account_type": account_type,
                "company_ids": [Command.set(self.company.ids)]}
        if tag:
            vals["tag_ids"] = [Command.set(
                self.env.ref("l10n_cz_fs.account_tag_vzz_%s" % tag).ids)]
        return self.env["account.account"].create(vals)

    def _post(self, lines, date="2025-03-01"):
        self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.misc.id, "date": date,
            "line_ids": [Command.create({
                "account_id": (a if isinstance(a, int) else self._acc(a).id),
                "debit": d, "credit": c}) for a, d, c in lines],
        }).action_post()

    def _statement(self, version):
        st = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        st.action_compute_lines()
        return st

    @staticmethod
    def _values(st):
        return {ln.code: ln.current_value for ln in st.line_ids}

    def _chart_codes(self):
        with open(file_path("l10n_cz/data/template/account.account-cz.csv"),
                  encoding="utf-8") as fh:
            return [r["code"] for r in csv.DictReader(fh)
                    if r["account_type"] != "off_balance"]

    # ------------------------------------------------------------------
    # 1. the two rozsahy cannot drift apart
    # ------------------------------------------------------------------
    def test_full_scope_covers_what_the_abridged_does(self):
        codes = self._chart_codes()

        def exempt(acc):
            return any(acc.startswith(p) for p in FULL_VS_ABRIDGED)

        for full, abridged in ((self.bs_full, self.bs_abr),
                               (self.pl_full, self.pl_abr)):
            wf, wa = _weights(full, codes), _weights(abridged, codes)
            shared = set(wf) & set(wa)
            self.assertGreater(len(shared), 20, "premise: codes are shared")
            seen_exempt = set()
            for code in sorted(shared):
                f = {a: n for a, n in wf[code].items() if n and not exempt(a)}
                a = {a: n for a, n in wa[code].items() if n and not exempt(a)}
                self.assertEqual(
                    f, a, "%s: %s covers other accounts in the plný rozsah "
                    "than in the zkrácený one" % (full.name, code))
                seen_exempt.update(
                    acc for acc in set(wf[code]) | set(wa[code])
                    if exempt(acc) and wf[code][acc] != wa[code][acc])
            if full == self.bs_full:
                # Every declared difference is real: a stale entry would
                # exempt an account from the comparison for no reason.
                for prefix in FULL_VS_ABRIDGED:
                    self.assertTrue(
                        any(acc.startswith(prefix) for acc in seen_exempt),
                        "%s is declared different but is not" % prefix)

    def test_full_scope_is_a_partition(self):
        """Each chart account on exactly one leaf of each side (two-sided
        accounts once per side, gated by sign), and A.V = *** of the VZZ."""
        codes = self._chart_codes()
        wb = _weights(self.bs_full, codes)
        wp = _weights(self.pl_full, codes)
        defs = {d.code: d for d in self.bs_full.line_def_ids}
        aktiva_leaves = [c for c, d in defs.items() if d.kind != "aggregate"
                         and d.sequence < defs["PASIVA"].sequence]
        pasiva_leaves = [c for c, d in defs.items() if d.kind != "aggregate"
                         and d.sequence > defs["PASIVA"].sequence]
        two_sided = set(self.bs_full._cssk_two_sided_prefixes())
        self.assertEqual(
            two_sided, {"221", "336", "341", "342", "343000", "345", "346",
                        "347", "373", "481"})
        for leaves in (aktiva_leaves, pasiva_leaves):
            reach = Counter()
            for leaf in leaves:
                for acc, n in wb[leaf].items():
                    reach[acc] += abs(n)
            self.assertFalse({a: n for a, n in reach.items() if n > 1},
                             "accounts on two leaves of one side")
        for acc in codes:
            if acc[:1] not in "01234":
                continue
            a, p = wb["AKTIVA"][acc], wb["PASIVA"][acc]
            if any(acc.startswith(t) for t in two_sided):
                self.assertEqual((a, p), (1, -1), acc)
            else:
                self.assertEqual(abs(a) + abs(p), 1, acc)
        for acc in codes:
            if acc[:1] in "56":
                self.assertEqual(wb["AV"][acc], wp["VHU"][acc], acc)
                self.assertEqual(abs(wp["VHU"][acc]), 1, acc)

    # ------------------------------------------------------------------
    # 2. a real ledger
    # ------------------------------------------------------------------
    def test_full_scope_ledger(self):
        iv1 = self._new_acc("665100", "Podíly - ovládaná", "income", "IV_1")
        v2 = self._new_acc("665200", "Výnosy z dluhopisů", "income", "V_2")
        vi1 = self._new_acc("662100", "Úroky - ovládaná", "income", "VI_1")
        j1 = self._new_acc("562100", "Úroky - ovládaná", "expense", "J_1")
        e2 = self._new_acc("559100", "OP k zásobám", "expense", "E_2")
        bank2 = self._new_acc("221900", "Kontokorent", "asset_cash")
        self._post([("221%", 100000, 0), ("411%", 0, 100000)], "2025-01-10")
        self._post([("022%", 60000, 0), ("221%", 0, 60000)])
        self._post([("132%", 5000, 0), ("321%", 0, 5000)])
        self._post([("311%", 50000, 0), ("602%", 0, 50000)])
        self._post([("524%", 3000, 0), ("527%", 1000, 0), ("331%", 0, 4000)])
        self._post([(e2.id, 700, 0), ("196%", 0, 700)])
        self._post([("559000", 300, 0), ("558%", 200, 0), ("391%", 0, 500)])
        self._post([("221%", 900, 0), (iv1.id, 0, 500), (v2.id, 0, 300),
                    ("665000", 0, 100)])
        self._post([("221%", 80, 0), (vi1.id, 0, 50), ("662000", 0, 30)])
        self._post([(j1.id, 40, 0), ("562000", 60, 0), ("221%", 0, 100)])
        self._post([("341%", 5000, 0), ("221%", 0, 5000)])
        self._post([("481%", 1200, 0), ("592%", 0, 1200)])
        self._post([("501%", 20000, 0), (bank2.id, 0, 20000)])

        pl = self._values(self._statement(self.pl_full))
        expected_pl = {
            "I": 50000, "A2": 20000, "D2_1": 3000, "D2_2": 1000, "D2": 4000,
            "E1": 0, "E2": 700, "E3": 500, "E": 1200, "PROV": 24800,
            "IV1": 500, "IV2": 100, "IV": 600, "V1": 0, "V2": 300, "V": 300,
            "VI1": 50, "VI2": 30, "VI": 80, "J1": 40, "J2": 60, "J": 100,
            "FIN": 880, "VHB": 25680, "L2": -1200, "VHU": 26880,
            "COBR": 50980,
        }
        for code, value in expected_pl.items():
            self.assertAlmostEqual(pl[code], value, 2, code)

        st = self._statement(self.bs_full)
        bs = self._values(st)
        expected_bs = {
            "BII2": 60000, "CI3_2": 4300, "CII2_1": 49500,
            "CII2_4_3": 5000, "CII1_4": 1200, "CII1": 1200,
            "CIV2": 35880, "AKTIVA": 155880,
            "AI1": 100000, "AV": 26880, "CIIP4": 5000, "CIIP8_3": 4000,
            "CIIP2": 20000, "CIIP8_5": 0, "CIP8": 0, "PASIVA": 155880,
        }
        for code, value in expected_bs.items():
            self.assertAlmostEqual(bs[code], value, 2, code)
        zasoby = st.line_ids.filtered(lambda ln: ln.code == "CI3_2")
        self.assertAlmostEqual(zasoby.gross_value, 5000, 2)
        self.assertAlmostEqual(zasoby.correction_value, 700, 2)
        self.assertEqual(st.unmapped_count, 0, st.unmapped_note)
        for code in ("CIV2", "CIIP2", "CII2_4_3"):
            line = st.line_ids.filtered(lambda ln, c=code: ln.code == c)
            self.assertTrue(line.source_reconciles,
                            "%s: the drill-down opens only the accounts on "
                            "this side" % code)

        # The zkrácený VZZ reads the same ledger to the same totals; only
        # IV. differs, because it still holds V.
        abr = self._values(self._statement(self.pl_abr))
        for code in set(abr) & set(pl):
            if code == "IV":
                self.assertAlmostEqual(abr[code], pl["IV"] + pl["V"], 2)
            else:
                self.assertAlmostEqual(abr[code], pl[code], 2, code)

    def test_one_split_tag_per_account(self):
        account = self._new_acc("665300", "Výnosy", "income", "IV_1")
        with self.assertRaises(ValidationError):
            account.tag_ids = [Command.link(
                self.env.ref("l10n_cz_fs.account_tag_vzz_V_1").id)]

    # ------------------------------------------------------------------
    # 3. defaults and export
    # ------------------------------------------------------------------
    def test_new_statement_defaults_to_full_scope(self):
        Statement = self.env["cssk.fs.statement"].with_company(self.company)
        for kind, full in (("balance_sheet", self.bs_full),
                           ("profit_loss", self.pl_full)):
            vals = Statement.with_context(fs_create_kind=kind).default_get(
                ["version_id", "date_from", "date_to"])
            self.assertEqual(vals.get("version_id"), full.id, kind)
        vals = Statement.with_context(
            fs_create_kind="balance_sheet",
            default_version_id=self.bs_abr.id).default_get(
            ["version_id", "date_from", "date_to"])
        self.assertEqual(vals["version_id"], self.bs_abr.id,
                         "an explicitly requested zkrácený version stays")
        self.assertEqual(self.bs_abr.l10n_cz_fs_scope, "abridged")
        self.assertEqual(self.bs_full.l10n_cz_fs_scope, "full")

    def test_export_states_the_rozsah(self):
        for version, rozsah in ((self.bs_full, "P"), (self.pl_abr, "Z")):
            st = self._statement(version)
            st.action_export_xml()
            root = etree.fromstring(
                base64.b64decode(st.xml_attachment_id.datas))
            self.assertEqual(root.findtext(".//Rozsah"), rozsah)

    def test_upgrade_names_the_existing_versions(self):
        self.env.cr.execute(
            "UPDATE cssk_fs_statement_version SET l10n_cz_fs_scope = NULL, "
            "name = 'Rozvaha 2025' WHERE id = %s", (self.bs_abr.id,))
        self.env.cr.execute(
            "UPDATE cssk_fs_statement_version SET l10n_cz_fs_scope = NULL, "
            "name = 'Můj výkaz' WHERE id = %s", (self.pl_abr.id,))
        self.env.invalidate_all()
        path = file_path("l10n_cz_fs/migrations/19.0.1.2.0/post-migrate.py")
        spec = importlib.util.spec_from_file_location("cz_fs_mig_120", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.migrate(self.env.cr, "19.0.1.1.2")
        self.env.invalidate_all()
        self.assertEqual(self.bs_abr.l10n_cz_fs_scope, "abridged")
        self.assertEqual(self.bs_abr.name, "Rozvaha 2025 (zkrácený rozsah)")
        self.assertEqual(self.pl_abr.l10n_cz_fs_scope, "abridged")
        self.assertEqual(self.pl_abr.name, "Můj výkaz",
                         "an administrator's own name stays")
