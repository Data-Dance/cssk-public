# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One UZPODv14 mapping, checked from both ends.

The module has two consumers of the same statutory form: ``l10n.sk.uzpod``,
which writes the filed XML straight from ``models/uzpod14_rows.py``, and a
``cssk.fs.statement`` version record, which renders the same form as a
drillable on-screen tree. Two mappings of one form is two chances to be wrong,
and the divergence is invisible from inside: the balance sheet still foots and
still balances, because A.VIII used to be a plug that absorbed whatever the
rest came to. It cost 47 of 114 súvaha rows before anybody compared them —
r043/r044/r045 each claimed the whole of 311-315, tripling the receivable.

The version's leaf rows are therefore generated from the reference by
``tools/gen_uzpod_v14_version.py``, and these tests are what keeps them there.

Coverage alone is not enough to prove the two agree, which is the point of
``test_each_aggregate_carries_the_same_weights_as_the_filed_row``: the same
SET of account codes can still produce a different number if a code is claimed
by two sibling rows, or claimed with a different sign. Weights per code,
summed over the transitive leaves, are what actually has to match.
"""

import os
import re
from collections import Counter

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_sk_fs.models.uzpod14_rows import (
    CLAIMED_ANALYTICS, SUVAHA_AKTIVA, SUVAHA_PASIVA, TWO_SIDED, VZS,
)

# A.VIII is the current-year result and the one row deliberately NOT taken
# from the reference table, because the reference does not take it from there
# either: ``l10n.sk.uzpod`` overrides r100 with the MOVEMENT of triedy 5/6 so
# that r100 == VZS r61 even when last year's classes are not yet closed to
# účet 431. The version record says the same thing as a movement-basis leaf.
RESULT_ROW = "s100"
# r079 and r080 are likewise computed by the export rather than read off the
# table (r079 = r080 + r101 + r141; r080 = capital accounts + the result), and
# the version says both as aggregates.
EXPORT_OVERRIDES = {"s079", "s080"}

# Rows where the FILED mapping's total does not equal the sum of its own
# components. Until 19.0.1.5.0 there were four (098000, 481000, 255100,
# 473100): the totals carried their own account lists and drifted from their
# leaves. They are now ``_SUM`` roll-ups of the leaves and cannot drift.
#
# What is left is not a defect: the filed r61 (and
# A.VIII with it) is literally ``-5,-6``, the WHOLE of classes 5 and 6, while
# the tree adds up the rows it shows. A class-5 account that no VZS row names
# therefore reaches the filed result and not the tree — which is the right way
# round for a filing, and exactly what the framework's unmapped-code
# diagnostic exists to surface on screen. Codes 500000/600000 stand for that
# residue in the synthetic chart these tests compare over.
KNOWN_FILED_GAPS = {
    "500000": {"v61"},
    "600000": {"v61"},
}


def _coverage_of_reference_row(code, atoms):
    """What the filed export's row takes off the synthetic chart."""
    ref = _REFERENCE_ROWS[code]
    cov = _coverage(ref[0], atoms)
    # A cond's mode is a FILTER on which accounts of the range take part; its
    # ``sign`` is the weight. Folding the mode into the weight would say that
    # ``neg_each, -1`` and the version's own ``-341`` token disagree, when
    # they are two spellings of the same thing: both multiply a credit balance
    # by -1 and so report the payable positively.
    for low, _high, _mode, sign in ref[1] or []:
        cov.update({c: sign for c, _t in atoms if c.startswith(low)})
    if len(ref) > 2:
        cov.update(_coverage(ref[2], atoms))
        for low, _high, _mode, sign in (ref[3] or []):
            cov.update({c: sign for c, _t in atoms if c.startswith(low)})
    return Counter({k: v for k, v in cov.items() if v})


_REFERENCE_ROWS = {}
for _i, _row in enumerate(SUVAHA_AKTIVA, start=1):
    _REFERENCE_ROWS["s%03d" % _i] = _row
for _i, _row in enumerate(SUVAHA_PASIVA, start=1):
    _REFERENCE_ROWS["s%03d" % (78 + _i)] = _row
for _i, _row in enumerate(VZS, start=1):
    _REFERENCE_ROWS["v%02d" % _i] = _row


def _atoms(all_tokens):
    """A synthetic chart fine enough to tell every token in play apart.

    The two mappings describe the same rows at different granularity: a total
    says ``665`` where its components say ``665&IX_1``, ``665&IX_2`` and
    ``665!IX_1!IX_2``, and ``51`` where they say ``501``..``507``. Comparing
    the token strings calls those different when they are the same set of
    money. So instead: invent one account per distinct token, tagged every way
    any token asks about, and compare what each formula COVERS.

    Returns ``[(code, {tags})]``.
    """
    tags = set()
    for tok in all_tokens:
        for _op, name in re.findall(r"([&!])([A-Za-z0-9_]+)", tok):
            tags.add(name)
    codes = {re.match(r"[0-9]*", tok).group(0) for tok in all_tokens}
    codes = {c for c in codes if c}
    out = []
    for code in sorted(codes):
        # pad so a short prefix ('51') and a long one ('501000') can both be
        # exercised, and give each tag its own account so an & and a ! token
        # never collapse onto the same one.
        base = (code + "000000")[:6]
        out.append((base, frozenset()))
        for tag in sorted(tags):
            out.append((base + "#" + tag, frozenset([tag])))
    return out


def _covers(token, code, code_tags):
    """Does one formula token take this synthetic account?"""
    negated = token.startswith("-")
    token = token.lstrip("-")
    include, exclude = None, set()
    match = re.match(r"([0-9]+)(.*)", token)
    prefix, rest = (match.group(1), match.group(2)) if match else (token, "")
    for op, name in re.findall(r"([&!])([A-Za-z0-9_]+)", rest):
        if op == "&":
            include = (include or set()) | {name}
        else:
            exclude.add(name)
    if not code.startswith(prefix):
        return 0
    if include is not None and not (code_tags & include):
        return 0
    if code_tags & exclude:
        return 0
    return -1 if negated else 1


def _coverage(formula, atoms, negate=False):
    """``{synthetic account: signed count}`` — what a formula actually takes."""
    out = Counter()
    for tok in (formula or "").split(","):
        tok = tok.strip()
        if not tok:
            continue
        for code, code_tags in atoms:
            weight = _covers(tok, code, code_tags)
            if weight:
                out[code] += -weight if negate else weight
    return out


def _weights(formula, negate=False):
    """``{account_code_prefix: signed count}`` for one formula.

    A Counter, not a set: an account claimed by two rows of the same subtree
    is the failure this exists to catch, and set equality cannot see it.
    """
    out = Counter()
    for tok in (formula or "").split(","):
        tok = tok.strip()
        if not tok:
            continue
        sign = -1 if tok.startswith("-") else 1
        code = tok.lstrip("-")
        # tag filters ride along with the code; they narrow WHICH accounts a
        # prefix takes, so they belong in the key rather than being stripped.
        out[code] += -sign if negate else sign
    return out


def _cond_weights(conds):
    """Range conds as the signed tokens the version stores them as.

    The reference keeps the 341-347 receivable/payable split out of the
    formula string, in ``[low, high, mode, sign]`` terms; the version says the
    same thing as a signed token that the evaluator's sign gate acts on. Both
    have to be counted or the two look different when they are not.
    """
    out = Counter()
    for low, _high, mode, sign in conds or []:
        if mode == "pos_each" and sign == 1:
            out[low] += 1
        elif mode == "neg_each" and sign == -1:
            out[low] -= 1
        elif mode == "neg_each" and sign == 1:
            # r079 SPOLU carries this alongside its -1 twin over the same
            # range, so the pair cancels; counted so it cancels here too.
            out[low] += 1
    return out


def _all_tokens():
    """Every token either mapping mentions, for building the synthetic chart."""
    toks = set()
    for rows, cols in ((SUVAHA_AKTIVA, (0, 2)), (SUVAHA_PASIVA, (0,)),
                       (VZS, (0,))):
        for row in rows:
            for col in cols:
                for tok in (row[col] or "").split(","):
                    if tok.strip():
                        toks.add(tok.strip().lstrip("-"))
            for low, _high, _mode, _sign in (row[1] or []):
                toks.add(low)
    return toks


def _reference_weights():
    """``{row code: Counter}`` for every row of the filed export's tables."""
    ref = {}
    for i, row in enumerate(SUVAHA_AKTIVA, start=1):
        w = _weights(row[0])
        w.update(_cond_weights(row[1]))
        # the korekcia column is subtracted from the gross, so its accounts
        # enter the row's net weight negated relative to how it stores them
        w.update(_weights(row[2]))
        w.update(_cond_weights(row[3]))
        ref["s%03d" % i] = w
    for i, row in enumerate(SUVAHA_PASIVA, start=1):
        w = _weights(row[0])
        w.update(_cond_weights(row[1]))
        ref["s%03d" % (78 + i)] = w
    for i, row in enumerate(VZS, start=1):
        w = _weights(row[0])
        w.update(_cond_weights(row[1]))
        ref["v%02d" % i] = w
    return {k: Counter({c: n for c, n in v.items() if n}) for k, v in ref.items()}


@tagged("post_install", "-at_install")
class TestUzpodOneMapping(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.version = cls.env.ref("l10n_sk_fs.uzpod_v14")
        cls.defs = {d.code: d for d in cls.version.line_def_ids}
        cls.ref = _reference_weights()
        cls.atoms = _atoms(_all_tokens())

    def _leaf_coverage(self, code, seen=None):
        """What a row takes off the synthetic chart: its own accounts, or its
        leaves' if it is a total."""
        seen = seen if seen is not None else set()
        self.assertNotIn(code, seen, "cycle through %s" % code)
        seen = seen | {code}
        ldef = self.defs[code]
        if ldef.kind == "aggregate":
            total = Counter()
            for ref_code, sign in self._terms(ldef.aggregate_formula):
                for key, val in self._leaf_coverage(ref_code, seen).items():
                    total[key] += sign * val
            return total
        cov = _coverage(ldef.account_formula, self.atoms)
        cov.update(_coverage(ldef.account_formula_correction, self.atoms,
                             negate=True))
        return cov

    @staticmethod
    def _terms(formula):
        """``[(code, +1/-1)]`` for an aggregate formula, honouring brackets.

        Only the shapes the form actually uses: sums, differences, and one
        parenthesised group that a leading minus distributes over.
        """
        out, sign, depth_sign = [], 1, 1
        for tok in re.findall(r"[A-Za-z_]\w*|[-+()]", formula or ""):
            if tok == "+":
                sign = 1
            elif tok == "-":
                sign = -1
            elif tok == "(":
                depth_sign = sign
                sign = 1
            elif tok == ")":
                depth_sign = 1
                sign = 1
            else:
                out.append((tok, sign * depth_sign))
                sign = 1
        return out

    def test_every_leaf_formula_is_the_filed_export_s_formula(self):
        """A leaf row must say exactly what the filed XML says for that row.

        Not "covers the same accounts" — the same string, so nobody can
        hand-edit the data file into a second mapping again. Regenerate with
        ``tools/gen_uzpod_v14_version.py`` if the reference table moves.
        """
        mismatched = []
        for code, ldef in sorted(self.defs.items()):
            if ldef.kind != "accounts" or code == RESULT_ROW:
                continue
            got = _weights(ldef.account_formula)
            got.update(_weights(ldef.account_formula_correction, negate=True))
            if got != self.ref[code]:
                mismatched.append(code)
        self.assertFalse(
            mismatched,
            "leaf rows that no longer match uzpod14_rows.py: %s" % mismatched)

    def test_each_aggregate_carries_the_same_weights_as_the_filed_row(self):
        """A total's leaves must add up to what the export computes directly.

        This is the check that account-code coverage alone cannot make: an
        account claimed by two sibling rows is counted twice here and once
        there, and set equality sees nothing. Comparing signed COUNTS over a
        synthetic chart catches multiplicity and sign, and comparing accounts
        rather than tokens stops a total that says ``665`` from looking
        different to leaves that partition it into ``665&IX_1`` /
        ``665&IX_2`` / ``665!IX_1!IX_2``.

        The exceptions are gaps in the FILED mapping, listed one by one in
        KNOWN_FILED_GAPS with what each one costs. They are not ours to fix
        quietly: changing that table changes filed figures.
        """
        bad = {}
        for code, ldef in sorted(self.defs.items()):
            if ldef.kind != "aggregate" or code in EXPORT_OVERRIDES:
                continue
            got = self._leaf_coverage(code)
            want = _coverage_of_reference_row(code, self.atoms)
            diff = {k: (want.get(k, 0), got.get(k, 0))
                    for k in set(want) | set(got)
                    if want.get(k, 0) != got.get(k, 0)}
            expected = {a for a, rows in KNOWN_FILED_GAPS.items()
                        if code in rows}
            unexplained = {k: v for k, v in diff.items()
                           if k.split("#")[0] not in expected}
            if unexplained:
                bad[code] = unexplained
        self.assertFalse(
            bad, "aggregate rows disagree with the filed export "
                 "(account: filed weight vs. tree weight): %s" % bad)

    def test_no_row_the_filed_export_reads_is_manual(self):
        """A manual row shows 0 until somebody types a figure, while the filed
        XML reads the same row off the ledger. s113 and v01 sat like that."""
        manual = sorted(
            code for code, ldef in self.defs.items()
            if ldef.kind == "manual" and code in self.ref
            and any(self.ref[code].values()))
        self.assertFalse(
            manual, "manual rows the filed export computes: %s" % manual)

    def test_the_result_row_is_not_a_plug(self):
        """A.VIII must be read off triedy 5/6, not derived from the sheet.

        As a plug (``s001 - the other passive rows``) it absorbs every mapping
        error on the passive side and the sheet still balances, which is how
        the 47 divergent rows went unnoticed. It also has to equal VZS r61,
        which a plug only does by luck.
        """
        result = self.defs[RESULT_ROW]
        self.assertEqual(result.kind, "accounts")
        self.assertEqual(result.account_formula, "-5,-6")
        self.assertEqual(result.basis, "movement",
                         "the result is the period's movement, not a balance")

    def test_the_generator_reproduces_the_checked_in_file(self):
        """The data file is generated; prove it still is.

        A hand edit that the two tests above happen not to catch — a renamed
        row, a changed sequence — would otherwise drift away from the script
        silently, and the next regeneration would revert it without warning.
        """
        import subprocess
        import sys
        root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        script = os.path.join(root, "tools", "gen_uzpod_v14_version.py")
        data = os.path.join(root, "l10n_sk_fs", "data",
                            "cssk_uzpod_v14_version_data.xml")
        if not os.path.exists(script):
            self.skipTest("running from an installed copy without tools/")
        before = open(data, encoding="utf-8").read()
        try:
            subprocess.run([sys.executable, script], cwd=root, check=True,
                           capture_output=True)
            after = open(data, encoding="utf-8").read()
        finally:
            open(data, "w", encoding="utf-8").write(before)
        self.assertEqual(
            before, after,
            "cssk_uzpod_v14_version_data.xml differs from what "
            "tools/gen_uzpod_v14_version.py produces — re-run it")

    def test_the_screen_claims_the_same_analytics_as_the_filed_export(self):
        """Both matchers must absorb analytics the same way, or they diverge.

        ``022000`` means "022 and its analytics, except those another row
        names". Which analytics are "named" is the whole content of that rule,
        and the two mappings compute it separately — the export in
        ``uzpod14_rows._claimed_analytics``, the statement from the version's
        own formulas. They agree only as long as both mean "six-character
        codes that are not a main account".
        """
        from odoo.addons.l10n_sk_fs.models.uzpod14_rows import CLAIMED_ANALYTICS
        st = self.env["cssk.fs.statement"].new({
            "company_id": self.env.company.id,
            "version_id": self.version.id,
        })
        self.assertEqual(st._cssk_claimed_codes(), CLAIMED_ANALYTICS)
        self.assertFalse(
            [c for c in CLAIMED_ANALYTICS if c.endswith("000")],
            "a main account must not claim against itself: 013000 would then "
            "exclude the account coded 013000 and the row would report zero")

    def test_every_row_carries_the_tlacivo_s_own_caption(self):
        """Labels come from the form, not from a transcription of it.

        The first pass took them from a plain pdftotext dump, where a two-line
        caption bleeds into the row below — "Poskytnuté" sat on r009 and r010
        read "7. preddavky na dlhodobý nehmotný majetok". About a third of the
        form was shifted like that, and a shifted caption is worse than a
        missing one: it names the row above's account list while looking
        perfectly ordinary.
        """
        import os

        from odoo.tools.misc import file_path

        path = file_path("l10n_sk_fs/data/uzpod14_row_labels.tsv")
        labels = {}
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                code, _, label = line.rstrip("\n").partition("\t")
                if code and label:
                    labels[code] = label
        self.assertEqual(len(labels), 206, os.path.basename(path))

        wrong = {code: (ldef.name, labels.get(code))
                 for code, ldef in sorted(self.defs.items())
                 if ldef.name != labels.get(code)}
        self.assertFalse(
            wrong, "rows whose caption is not the tlačivo's "
                   "(row: shipped vs. tlačivo): %s" % wrong)

    def test_no_caption_carries_another_row_s_text(self):
        """The signature of the leak, asserted directly.

        A bled caption shows up two ways: a row marker stranded inside the
        text ("Pohľadávky z obchodné1.b. ho styku"), and page furniture that
        is not a caption at all.
        """
        stranded = {c: d.name for c, d in self.defs.items()
                    if re.search(r"[a-záäčďéíĺľňóôŕšťúýž]\d{1,2}\.[a-c]?\.?\s",
                                 d.name)}
        self.assertFalse(stranded, "a row marker inside a caption: %s" % stranded)
        furniture = {c: d.name for c, d in self.defs.items()
                     if re.search(r"Korekcia|Brutto|Netto|MF SR|Strana \d|"
                                  r"UZPODv14|Á Ä", d.name)}
        self.assertFalse(furniture, "page furniture in a caption: %s" % furniture)


# Balance-sheet accounts of the l10n_sk chart that deliberately reach no
# Súvaha row. 431000 stands against the unclosed opening balance of triedy
# 5/6 and r100 takes the result from their movement instead (see
# ``l10n.sk.uzpod._cssk_unmapped_report``). 395000 is a vnútorné zúčtovanie
# between a company's own units: it nets to zero in a closed ledger, and a
# balance left on it is an error the unmapped diagnostic should show rather
# than a row should absorb.
NOT_REPORTED = {"395000", "431000"}


@tagged("post_install", "-at_install")
class TestUzpodChartCoverage(TransactionCase):
    """The mapping against the chart it is used with, account by account.

    Matching the two mappings to each other proves they agree, not that
    either is right: in 19.0.1.4.0 both named 16 codes the l10n_sk chart does
    not have (091120 where the chart says 091200, 322300 for 322100, ...) and
    let 34 of its balance-sheet accounts reach no row at all — 325000 Iné
    záväzky, 461000 bank loans, 471200, 473100 issued bonds among them. The
    sheet still balanced, because the leftover went nowhere on either side
    only when it happened to net to zero.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import csv

        from odoo.tools.misc import file_path

        path = file_path("l10n_sk/data/template/account.account-sk.csv")
        with open(path, encoding="utf-8") as fh:
            cls.chart = {row["code"]: row["name"] for row in csv.DictReader(fh)}
        cls.uzpod = cls.env["l10n.sk.uzpod"]
        cls.leaves = {}
        version = cls.env.ref("l10n_sk_fs.uzpod_v14")
        leaf_codes = {d.code for d in version.line_def_ids
                      if d.kind == "accounts" and d.code.startswith("s")}
        leaf_codes.discard(RESULT_ROW)
        for code in leaf_codes:
            row = _REFERENCE_ROWS[code]
            cells = [(row[0], row[1], "")]
            if len(row) > 2:
                cells.append((row[2], row[3], "korekcia "))
            cls.leaves[code] = cells

    def _landing(self, account):
        """``[row label]`` of every leaf cell that takes this account."""
        out = []
        for code, cells in sorted(self.leaves.items()):
            for formula, conds, col in cells:
                for tok in (formula or "").split(","):
                    _neg, prefix, _inc, _exc = self.uzpod._cssk_split_token(tok, {})
                    if prefix and self.uzpod._cssk_code_matches(
                            account, prefix, CLAIMED_ANALYTICS):
                        out.append(col + code)
                if any(low <= account < high for low, high, _m, _s in conds):
                    out.append(col + code)
        return out

    def test_every_balance_sheet_account_reaches_a_row(self):
        missing = {code: name for code, name in sorted(self.chart.items())
                   if code[:1] in "01234" and code not in NOT_REPORTED
                   and not self._landing(code)}
        self.assertFalse(missing, "l10n_sk accounts on no Súvaha row: %s" % missing)

    def test_no_row_names_an_account_the_chart_does_not_have(self):
        dead = {}
        for code, cells in sorted(self.leaves.items()):
            for formula, _conds, col in cells:
                for tok in (formula or "").split(","):
                    _neg, prefix, _inc, _exc = self.uzpod._cssk_split_token(tok, {})
                    if prefix and not any(
                            self.uzpod._cssk_code_matches(a, prefix, CLAIMED_ANALYTICS)
                            for a in self.chart):
                        dead.setdefault(col + code, []).append(tok.strip())
        self.assertFalse(dead, "tokens matching no l10n_sk account: %s" % dead)

    def test_an_account_lands_on_one_row_or_is_gated(self):
        """Two rows taking one balance double it, unless the balance sign
        decides between them (``TWO_SIDED``, and the 341-347 conds)."""
        doubled = {}
        for account in sorted(self.chart):
            if account[:1] not in "01234":
                continue
            rows = self._landing(account)
            if len(rows) > 1 and account not in TWO_SIDED and not (
                    "341" <= account < "348"):
                doubled[account] = rows
        self.assertFalse(doubled, "accounts on two rows at once: %s" % doubled)

    def test_the_export_gates_the_same_accounts_as_the_screen(self):
        st = self.env["cssk.fs.statement"].new({
            "company_id": self.env.company.id,
            "version_id": self.env.ref("l10n_sk_fs.uzpod_v14").id,
        })
        screen = set(st._cssk_two_sided_prefixes())
        # the screen also gates the 341-347 cond tokens the generator emits
        self.assertEqual(screen - {"341", "342", "343", "345", "346", "347"},
                         set(TWO_SIDED))

    def test_a_deferred_tax_asset_is_filed_on_the_asset_side_only(self):
        balances = {"481000": 100.0}
        asset = SUVAHA_AKTIVA[52 - 1]
        liability = SUVAHA_PASIVA[117 - 79]
        self.assertEqual(self.uzpod._eval(asset[0], asset[1], balances), 100.0)
        self.assertEqual(self.uzpod._eval(liability[0], liability[1], balances), 0.0)
        balances = {"481000": -40.0}
        self.assertEqual(self.uzpod._eval(asset[0], asset[1], balances), 0.0)
        self.assertEqual(self.uzpod._eval(liability[0], liability[1], balances), 40.0)

    def test_an_allowance_reduces_the_netto(self):
        """Korekcia is subtracted from brutto, so an opravná položka (a credit
        balance) must enter it positive. 391336 and 391700 were carried
        unsigned and raised r062/r051 by the allowance instead."""
        for row_no, account in ((62, "391336"), (51, "391700")):
            row = SUVAHA_AKTIVA[row_no - 1]
            korekcia = self.uzpod._eval(row[2], row[3], {account: -30.0})
            self.assertEqual(korekcia, 30.0, "r%03d / %s" % (row_no, account))
