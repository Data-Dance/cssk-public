# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_open


def filed_returns():
    """The 38 returns a real company actually submitted. See the README."""
    with file_open(
        "l10n_sk_vat_return/tests/fixtures/filed_vat_returns.json", "r"
    ) as fh:
        return json.load(fh)


@tagged("post_install", "-at_install")
class TestFiledReturns(TransactionCase):
    """Check this module against returns that were really filed.

    A localisation validated against constructed cases proves it agrees with
    whoever constructed them. These figures were submitted to the tax office.
    """

    def test_the_fixture_still_says_what_the_tests_rely_on(self):
        """Guard the oracle itself.

        Every assertion below rests on this file, so the file's own shape is
        worth asserting before anything is concluded from it — a fixture that
        silently loses a field takes its tests with it, and they go green.
        """
        data = filed_returns()
        self.assertEqual(len(data), 38, "the fixture changed size")
        for row in data:
            for key in ("period", "form", "kind", "filed_on", "lines"):
                self.assertIn(key, row, "a filing lost its %s" % key)
            self.assertTrue(row["lines"], "a filing has no line amounts at all")
        self.assertEqual(
            sorted({r["kind"] for r in data}), ["D", "R"],
            "the fixture should carry both a riadny and a dodatočné return",
        )

    def test_the_form_vintage_changes_on_1_july_2025(self):
        """The fact the module currently gets wrong.

        32 of the 38 filings are on `DPH2021` and 6 on `DPH2025`, and the
        switch is exactly at 2025-07 — visible on identical amounts either side
        of it, so it cannot be an effect of the company's own activity:

            2025-06  DPH2021  r09  12.59  r10  2.90
            2025-07  DPH2025  r09b 12.59  r10b 2.90
        """
        by_period = {r["period"]: r for r in filed_returns()}
        for period, expected in (("2025-05", "DPH2021"), ("2025-06", "DPH2021"),
                                 ("2025-07", "DPH2025"), ("2025-08", "DPH2025")):
            self.assertEqual(
                by_period[period]["form"], expected,
                "%s should have been filed on %s" % (period, expected),
            )
        june, july = by_period["2025-06"]["lines"], by_period["2025-07"]["lines"]
        self.assertEqual(
            (june.get("r09"), june.get("r09b")), (12.59, None),
            "before the change the standard reverse charge is on r09",
        )
        self.assertEqual(
            (july.get("r09"), july.get("r09b")), (None, 12.59),
            "after it, the same amount is on r09b",
        )

    def test_where_the_version_table_starts_and_what_it_leaves_out(self):
        """Every filed period must resolve to exactly one version.

        The fixture found the gap on its first run: the module shipped versions
        from **2024-01-01** while the company filed from **2022-12**, so
        fourteen filed periods had no version at all and a return computed for
        them produced nothing rather than something wrong. This asserted the
        count of 14 so that closing the gap would fail the test and prompt an
        update — which is exactly what happened.

        The gap closed as a side effect of a different fix. Splitting the
        pre-July-2025 vzor out of the 2025 grid meant dating the older record
        from **2011-01-01**, when the 20 % standard rate came in, and that
        covers every period the company has ever filed. So the assertion is now
        the one worth keeping: **nothing uncovered, and nothing covered twice.**
        Overlap matters as much as the gap — two versions matching one period
        makes which grid a return uses depend on search order.
        """
        Version = self.env["cssk.vat.return.version"]
        earliest = Version.search(
            [("country_id.code", "=", "SK")], order="valid_from", limit=1)
        self.assertTrue(earliest, "no SK return version is installed at all")

        uncovered, ambiguous = [], []
        for row in filed_returns():
            date_from = row["period"] + "-01"
            found = Version.search([
                ("country_id.code", "=", "SK"),
                ("valid_from", "<=", date_from),
                "|", ("valid_to", "=", False), ("valid_to", ">=", date_from),
            ])
            if not found:
                uncovered.append(row["period"])
            elif len(found) > 1:
                ambiguous.append((row["period"], found.mapped("name")))

        self.assertFalse(
            uncovered,
            "filed periods with no version at all — a return computed for "
            "them produces nothing rather than something wrong: %s"
            % (uncovered,),
        )
        self.assertFalse(
            ambiguous,
            "filed periods matching more than one version, so which grid is "
            "used depends on search order: %s" % (ambiguous,),
        )
        self.assertLessEqual(
            str(earliest.valid_from), min(r["period"] for r in filed_returns()),
            "the earliest version starts after the earliest filed period",
        )

    def test_the_version_chosen_matches_the_form_actually_filed(self):
        """The real regression test. It used to skip itself; now it runs.

        The module had ONE version from 2025-01-01 while the company filed on
        two — `DPH2021` through June, `DPH2025` from July — so for the first
        six months of 2025 the standard reverse charge was reported on `r09b`,
        a band those periods did not have: right totals, wrong return.

        The skip was written to clear itself the moment a second 2025 version
        existed, and it has. What it was waiting on — whether the pre-July vzor
        carried a single combined reverse-charge band — is now settled from
        `dph2021.xsd`, which defines `r09`/`r10` and no lettered variants, and
        corroborated by the filings themselves: `r09`/`r10` in 15 periods to
        2025-06, `r09b`/`r10b` in 6 periods from 2025-07, no overlap either way.
        """
        Version = self.env["cssk.vat.return.version"]
        in_2025 = Version.search([
            ("country_id.code", "=", "SK"),
            ("valid_from", "<=", "2025-12-31"),
            "|", ("valid_to", "=", False), ("valid_to", ">=", "2025-01-01"),
        ])
        if len(in_2025) < 2:
            self.skipTest(
                "the module ships one version for all of 2025; the filed data "
                "shows two (DPH2021 to June, DPH2025 from July). Confirm "
                "whether the pre-July vzor had a single combined "
                "reverse-charge band, then split the version and this test "
                "runs by itself."
            )
        for row in filed_returns():
            if not row["period"].startswith("2025"):
                continue
            date_from = row["period"] + "-01"
            chosen = Version.search([
                ("country_id.code", "=", "SK"),
                ("valid_from", "<=", date_from),
                "|", ("valid_to", "=", False), ("valid_to", ">=", date_from),
            ], order="valid_from desc", limit=1)
            band, absent = (
                ("r09b", None) if row["form"] == "DPH2025" else ("r09", "r09b")
            )
            codes = chosen.line_def_ids.mapped("code")
            self.assertIn(
                band, codes,
                "%s was filed on %s, whose standard reverse-charge band is "
                "%s, but the chosen version %s does not define it"
                % (row["period"], row["form"], band, chosen.display_name),
            )
            # The negative half is the one that was actually broken: the old
            # grid DID define r09, so asserting only its presence passed
            # throughout the bug. What made the return wrong was r09b existing
            # in a period that had no such line for a supply to land on.
            if absent:
                self.assertNotIn(
                    absent, codes,
                    "%s was filed on %s, which has no %s at all, yet the "
                    "chosen version %s defines it — a reverse charge in this "
                    "period can still land on a line that did not exist"
                    % (row["period"], row["form"], absent, chosen.display_name),
                )
