# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..garnishment import NET_WAGE_CATEGORIES, garnishment_net_wage


@tagged("post_install", "-at_install")
class TestGarnishmentNetWage(TransactionCase):
    def test_net_wage_is_the_wage_less_premiums_and_the_advance(self):
        """§ 69 ods. 1 Exekučného poriadku: 1 500.00 less premiums of 216.00
        and an advance of 149.49 is 1 134.51. The child bonus of 200.00 is
        not wage (§ 118 ods. 2 Zákonníka práce) and changes nothing."""
        totals = {"GROSS": 1500.0, "SOCIALEMPLOYEE": -216.0,
                  "INCOMETAX": -149.49, "DED": -165.49, "CHILDBONUS": 200.0}
        self.assertEqual(garnishment_net_wage(totals), 1134.51)
        self.assertNotIn("CHILDBONUS", NET_WAGE_CATEGORIES)

    def test_the_employers_sick_pay_is_part_of_the_net_wage(self):
        """§ 89 ods. 1: income that replaces the remuneration for work."""
        totals = {"GROSS": 1500.0, "SOCIALEMPLOYEE": -216.0,
                  "INCOMETAX": -149.49, "SICKCOMP": 74.0, "CHILDBONUS": 100.0,
                  "MEALEMPLOYERCOST": 93.5, "ANNUALSETTLEMENT": 30.0}
        self.assertEqual(garnishment_net_wage(totals), 1208.51)

    def test_a_missing_category_counts_as_nothing(self):
        self.assertEqual(garnishment_net_wage({"GROSS": 700.0}), 700.0)

    def test_the_payslip_helper_reads_both_engines_namespaces(self):
        """A mapping on Enterprise, an object holding one on the OCA engine."""
        Mixin = self.env["l10n.sk.payslip.fund.mixin"]
        totals = {"GROSS": 1000.0, "SOCIALEMPLOYEE": -144.0,
                  "INCOMETAX": -67.15}

        class Browsable:
            dict = totals

        self.assertEqual(Mixin.l10n_sk_garnishment_net_wage(totals), 788.85)
        self.assertEqual(
            Mixin.l10n_sk_garnishment_net_wage(Browsable()), 788.85)
