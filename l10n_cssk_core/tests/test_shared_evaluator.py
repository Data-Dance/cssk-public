# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The one account-code matcher, and the diagnostic that catches silent drops.

The FS statement, the income-tax return and the SK Úč POD XML builder each used
to carry their own copy of "sum posted balances by account-code prefix". The
copies drifted, so the figures previewed on screen did not have to equal the
figures filed. These tests pin the conventions the single implementation now
has to honour for all three callers at once — above all the two that differ and
must NOT be normalised away: the income-tax return's inverted sign, and absorb
being opt-in so CZ row definitions keep their meaning.
"""
from odoo.tests.common import TransactionCase


class TestSharedEvaluator(TransactionCase):
    """Pure-function tests of the shared matcher (no ledger needed)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Any concrete model carrying the mixin exposes the shared methods.
        cls.ev = cls.env["cssk.statutory.submission.mixin"]
        cls.balances = {
            "022000": 100.0,
            "022001": 200.0,
            "022150": 400.0,   # explicitly claimed by another row
            "411000": -700.0,
            "131ved": 50.0,    # non-numeric analytic, as imported ledgers carry
        }

    # -- sign conventions ------------------------------------------------

    def test_fs_sign_convention(self):
        """FS: a bare prefix counts +1, a leading '-' counts −1."""
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("022", self.balances), 700.0, places=2)
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("-411", self.balances), 700.0, places=2)

    def test_income_tax_sign_convention_is_inverted(self):
        """The income-tax return reads the SAME formula the other way round.

        Its row definitions depend on a bare prefix counting −1 and '-'
        counting +1, so that the net comes out as a positive profit. Sharing
        one matcher must not quietly hand it the FS convention."""
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula(
                "022", self.balances, default_sign=-1.0), -700.0, places=2)
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula(
                "-411", self.balances, default_sign=-1.0), -700.0, places=2)

    def test_account_matched_twice_contributes_per_token(self):
        """Historical semantics every existing row definition relies on."""
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("02,022", self.balances),
            1400.0, places=2)

    # -- absorb is opt-in ------------------------------------------------

    def test_absorb_off_by_default(self):
        """Without ``claimed`` a 6-digit token is a plain prefix.

        l10n_cz_fs already uses 343000 beside 343001 and 343112. If absorb
        were on by default, 343000 would start swallowing its siblings and
        change figures on a filed Czech statement."""
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("022000", self.balances),
            100.0, places=2)

    def test_absorb_on_takes_unclaimed_analytics_only(self):
        """With ``claimed``, NNN000 takes every analytic of NNN that no other
        row names outright — including non-numeric ones — but never a claimed
        analytic, which would otherwise be counted on two rows at once."""
        total = self.ev._cssk_eval_formula(
            "022000", self.balances, claimed={"022150"})
        # 022000 + 022001, NOT 022150 (claimed elsewhere)
        self.assertAlmostEqual(total, 300.0, places=2)
        total = self.ev._cssk_eval_formula(
            "131000", self.balances, claimed=set())
        self.assertAlmostEqual(total, 50.0, places=2, msg="131ved absorbed")

    # -- conditional terms -----------------------------------------------

    def test_conditional_terms_gate_on_sign(self):
        """The receivable/payable split: a tax account lands on one row or the
        other according to the sign of its net."""
        bal = {"343000": 500.0}
        pos = [["343", "344", "pos", 1]]
        neg = [["343", "344", "neg", -1]]
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("", bal, conds=pos), 500.0, places=2)
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("", bal, conds=neg), 0.0, places=2)

    # -- the diagnostic --------------------------------------------------

    def test_unmapped_codes_finds_the_silent_drop(self):
        """An account no row covers contributes to nothing, and nothing warns.

        This is the failure that hid seven synthetics in the SK Úč POD row set
        until someone tied the statement back to the source system. A trial
        balance that foots to zero cannot detect it: a balanced ledger says
        nothing about whether every account reached a row."""
        cells = [("022000", []), ("-411", [])]
        unmapped = self.ev._cssk_unmapped_codes(
            self.balances, cells, claimed={"022150"})
        codes = [code for code, _bal in unmapped]
        self.assertIn("131ved", codes)
        self.assertIn("022150", codes, "claimed but routed to no row")
        self.assertNotIn("022001", codes, "absorbed by 022000")
        self.assertNotIn("411000", codes)

    def test_unmapped_codes_sorted_by_materiality(self):
        """Largest absolute balance first — the reviewer reads top-down."""
        bal = {"111": 5.0, "222": -9000.0, "333": 100.0}
        unmapped = self.ev._cssk_unmapped_codes(bal, [("999", [])])
        self.assertEqual([c for c, _b in unmapped], ["222", "333", "111"])

    def test_conds_count_as_coverage(self):
        """A code reached only by a conditional term is mapped, not missing."""
        bal = {"343000": 500.0}
        self.assertEqual(
            self.ev._cssk_unmapped_codes(
                bal, [("", [["343", "344", "pos", 1]])]),
            [])

    # -- regressions found in second-opinion review ----------------------

    def test_tag_ops_resolve_with_no_tags_configured(self):
        """The *ostatné* leaf must carry the full amount when nothing is tagged.

        ``665!IX_1!IX_2`` means "665 except the related-party tags". With no
        tags configured — the default, no-setup state — the exclusion is empty
        and the whole of 665 belongs on that row. An earlier draft only parsed
        the ``&``/``!`` operators when the tag map was non-empty, which left
        the token literal, matched no account code, and silently reported zero
        on precisely the case the split exists to handle."""
        bal = {"665000": 1000.0, "665001": 2000.0, "665100": 500.0}
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula(
                "-665!IX_1!IX_2", bal, claimed=set(), tag_codes={}),
            -3500.0, places=2, msg="ostatné leaf zeroed with an empty tag map")
        # and with a tag configured, the tagged account drops out
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula(
                "-665!IX_1!IX_2", bal, claimed=set(),
                tag_codes={"IX_1": {"665001"}, "IX_2": set()}),
            -1500.0, places=2)

    def test_tag_ops_are_opt_in_per_caller(self):
        """A caller that passes no tag map keeps the token LITERAL.

        The FS statement and the income-tax return never had tag support;
        their evaluators treated ``665!IX_1`` as a literal prefix that matches
        no account. Enabling the operators for them would change filed figures
        on any formula containing & or !. The switch is ``tag_codes is not
        None`` — an empty dict opts in (see the test above), omitting the
        argument stays out. Gating on truthiness instead conflates the two and
        breaks one caller whichever way it is set."""
        bal = {"665000": 1000.0, "665001": 2000.0, "665100": 500.0}
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("-665!IX_1!IX_2", bal), 0.0, places=2)
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula(
                "-665!IX_1!IX_2", bal, default_sign=-1.0), 0.0, places=2)

    def test_empty_prefix_token_matches_nothing(self):
        """A degenerate token contributes nothing instead of everything.

        ``"".startswith("")`` is True, so a stray bare '-' in a formula used to
        match EVERY account and negate the entire trial balance — a one-
        character typo away from a catastrophically wrong filing. No shipped
        row definition contains one, so this is a guard, not a fix."""
        bal = {"022000": 100.0, "411000": -700.0}
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("-", bal), 0.0, places=2)
        self.assertAlmostEqual(
            self.ev._cssk_eval_formula("022000,", bal), 100.0, places=2)
