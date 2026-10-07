# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Every account must reach EXACTLY ONE Súvaha leaf — the uniqueness half.

Two checks already guard this statement and neither can see a double-mapping:

* ``SUCET_BS`` asserts parent = Σ children. An account listed on two leaves is
  also listed twice on their common ancestor, so the subtotals reconcile
  perfectly while total assets are overstated. It validates internal
  consistency, not correctness.
* ``BS_UNMAPPED`` asks "does this account reach a row?". An account on two rows
  reaches one, so it is invisible there **by construction**.

"Reaches exactly one" is a third question and needs its own test. It found
221100 sitting on both A.III.9 (bank accounts maturing over one year) and
B.V.2 (current bank accounts) — small in money terms, but the class of bug is
silent and permanent, and this is the only thing that looks for it.

The coverage half of the partition — every account reaching AT LEAST one row —
is deliberately NOT asserted here. Several synthetics are known to reach none
(096, 395, 431, 461, 474, 325) pending a statutory decision, and runtime
``BS_UNMAPPED`` reports them against real data, which is where coverage is
better judged than against a demo chart.
"""
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_sk_fs.models.uzpod14_rows import (
    CLAIMED_ANALYTICS,
    SUVAHA_AKTIVA,
)
from odoo.addons.l10n_sk_fs.models.uzpod14_kontroly import SUCET_BS


class TestRowPartition(TransactionCase):
    """Static analysis of the row definitions — no ledger, no company."""

    #: Accounts on more than one AKTÍVA leaf, with the reason each is tolerated.
    #: Empty is the goal. An entry here is a KNOWN BUG awaiting a decision, not
    #: an exemption — remove it when the row definitions are corrected, and the
    #: test tightens automatically.
    # 221100 "Zablokované bankové účty (> 1 rok)" sat on A.III.9 and on B.V.2
    # (current bank accounts) and inflated total assets by its balance until
    # 19.0.1.5.0. Nothing is exempt now.
    KNOWN_DOUBLE_MAPPED = set()

    @staticmethod
    def _matches(code, prefix):
        """The absorb-aware matcher, mirroring cssk.statutory.submission.mixin.

        Duplicated deliberately: this test exists to check the row DATA, so it
        must not go through the code path whose behaviour it is validating.
        """
        if len(prefix) == 6 and prefix.endswith("000"):
            return code[:3] == prefix[:3] and code[:6] not in CLAIMED_ANALYTICS
        return code.startswith(prefix)

    def _leaf_rows(self):
        """AKTÍVA row numbers that are not a parent in any SUCET_BS relation."""
        parents = {parent for parent, _kids in SUCET_BS}
        return [rn for rn in range(1, len(SUVAHA_AKTIVA) + 1)
                if rn not in parents]

    def _placements(self, code, slot):
        """[(row_number, times_counted)] for one account in one column."""
        out = []
        for rn in self._leaf_rows():
            formula = SUVAHA_AKTIVA[rn - 1][slot] or ""
            hits = sum(
                1 for token in formula.split(",")
                if token.strip()
                and self._matches(code, token.strip().lstrip("-"))
            )
            if hits:
                out.append((rn, hits))
        return out

    def _chart_codes(self):
        """Codes of the installed SK chart, minus what a Súvaha never carries."""
        accounts = self.env["account.account"].search([])
        return sorted({
            a.code for a in accounts
            if a.code
            and a.account_type != "off_balance"
            and not a.code.startswith("7")      # závierkové / podsúvahové
            and a.code[:1] not in ("5", "6")    # náklady / výnosy → VZS
        })

    def test_no_account_reaches_two_aktiva_leaves(self):
        found = {}
        for code in self._chart_codes():
            for slot, column in ((0, "brutto"), (2, "korekcia")):
                placements = self._placements(code, slot)
                if sum(times for _rn, times in placements) > 1:
                    found.setdefault(code, []).append((column, placements))

        unexpected = {c: v for c, v in found.items()
                      if c not in self.KNOWN_DOUBLE_MAPPED}
        self.assertFalse(
            unexpected,
            "Account(s) counted on more than one Súvaha leaf, so total assets "
            "are overstated by their balance while SUCET_BS still reconciles:\n"
            + "\n".join(
                "  %s -> %s" % (code, placements)
                for code, placements in unexpected.items()
            ),
        )

    def test_known_double_mapped_still_reproduces(self):
        """The exemption list must not outlive the bug it documents.

        If a listed account stops being double-mapped, the fix has landed and
        the entry has to go — otherwise the list quietly becomes a place where
        real regressions can hide.
        """
        for code in self.KNOWN_DOUBLE_MAPPED:
            total = sum(
                times
                for slot in (0, 2)
                for _rn, times in self._placements(code, slot)
            )
            self.assertGreater(
                total, 1,
                "%s is no longer double-mapped — remove it from "
                "KNOWN_DOUBLE_MAPPED so the partition test tightens." % code,
            )
