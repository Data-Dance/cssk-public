# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The annual tax settlement: the child bonus already granted and § 38 ods. 7.

The reconciliations here take typed totals, so the same cases run on both
payroll engines.
"""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkTaxSettlementRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK settlement rules", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids,
                         lang="en_US")
        )

    def _settlement(self, year, advance, paid=0.0, children=0, base=20000.0, **vals):
        employee = self.env["hr.employee"].create(
            {
                "name": "Settlement %s %s %s" % (year, advance, paid),
                "company_id": self.company.id,
                "date_version": date(2024, 1, 1),
                "contract_date_start": date(2024, 1, 1),
            }
        )
        employee.version_id.l10n_sk_children_under_15 = children
        return self.env["l10n.sk.tax.reconciliation"].create(
            {
                "employee_id": employee.id,
                "company_id": self.company.id,
                "year": year,
                "gather_from_payslips": False,
                "annual_tax_base": base,
                "annual_advance_tax": advance,
                "annual_child_bonus_paid": paid,
                **vals,
            }
        )

    def _parameter(self, code, day):
        Parameter = self.env["hr.rule.parameter"]
        reader = getattr(Parameter, "_get_parameter_from_code", None) or \
            Parameter._get_parameter_value
        return reader(code, day)

    # 2024: 20 000 − 5 646,48 = 14 353,52, tax 19 % = 2 727,17.
    TAX_2024 = 2727.17
    # 2025: 20 000 − 5 753,79 = 14 246,21, tax 19 % = 2 706,78.
    TAX_2025 = 2706.78

    # ------------------------------------------------------------------
    # § 33 ods. 11 zákona 595/2003 as in force to 31. 12. 2024
    # ------------------------------------------------------------------
    def test_bonus_granted_during_2024_is_kept(self):
        """Tax year 2024: 1 820 granted, 12 × 140 = 1 680 recomputed.

        The taxpayer "nestráca nárok na už priznaný daňový bonus": nothing is
        taken back.
        """
        rz = self._settlement(2024, self.TAX_2024, paid=1820.0, children=1)
        self.assertEqual(rz.annual_tax, self.TAX_2024)
        self.assertEqual(rz.child_bonus_entitlement, 1820.0)
        self.assertEqual(rz.result_amount, 0.0)
        self.assertEqual(rz.result_type, "none")

    def test_bonus_still_due_for_2024_is_paid(self):
        """Tax year 2024: 1 500 granted, 1 680 due: 180 is paid out."""
        rz = self._settlement(2024, self.TAX_2024, paid=1500.0, children=1)
        self.assertEqual(rz.child_bonus_entitlement, 1680.0)
        self.assertEqual(rz.result_amount, 180.0)

    def test_bonus_overpaid_in_2025_is_taken_back(self):
        """From January 2025 the sentence is gone (§ 52zzzb ods. 6).

        1 300 granted, 12 × 100 = 1 200 recomputed: 100 is taken back.
        """
        rz = self._settlement(2025, self.TAX_2025, paid=1300.0, children=1)
        self.assertEqual(rz.annual_tax, self.TAX_2025)
        self.assertEqual(rz.child_bonus_entitlement, 1200.0)
        self.assertEqual(rz.result_amount, -100.0)
        self.assertEqual(rz.result_type, "nedoplatok")

    def test_keeping_the_granted_bonus_ends_with_2024(self):
        code = "l10n_sk_child_bonus_keep_granted"
        for day, kept in ((date(2023, 1, 1), True), (date(2024, 12, 31), True),
                          (date(2025, 1, 1), False), (date(2026, 12, 31), False)):
            with self.subTest(day=day):
                self.assertEqual(bool(self._parameter(code, day)), kept)

    # ------------------------------------------------------------------
    # § 38 ods. 7 zákona 595/2003: an underpayment of 5 EUR or less
    # ------------------------------------------------------------------
    def test_underpayment_up_to_five_euros_is_not_withheld(self):
        """Tax 2 706,78 against advances of 2 703,28: 3,50 is not withheld."""
        rz = self._settlement(2025, self.TAX_2025 - 3.50)
        self.assertEqual(rz.result_amount, 0.0)
        self.assertEqual(rz.result_type, "none")
        self.assertEqual(rz.tax_underpayment_waived, 3.50)

    def test_underpayment_of_exactly_five_euros_is_not_withheld(self):
        rz = self._settlement(2025, self.TAX_2025 - 5.00)
        self.assertEqual(rz.tax_underpayment_waived, 5.00)
        self.assertEqual(rz.result_amount, 0.0)

    def test_underpayment_over_five_euros_is_withheld(self):
        rz = self._settlement(2025, self.TAX_2025 - 5.01)
        self.assertEqual(rz.tax_underpayment_waived, 0.0)
        self.assertEqual(rz.result_amount, -5.01)
        self.assertEqual(rz.result_type, "nedoplatok")

    def test_small_underpayment_is_withheld_when_a_share_of_tax_is_assigned(self):
        """§ 50, § 50aa: the tax has to be paid in full."""
        rz = self._settlement(2025, self.TAX_2025 - 3.50, assigns_tax_share=True)
        self.assertEqual(rz.tax_underpayment_waived, 0.0)
        self.assertEqual(rz.result_amount, -3.50)

    def test_small_underpayment_is_set_off_against_the_bonus_due(self):
        """100 of bonus still due: the 3,50 comes off it, 96,50 is paid."""
        rz = self._settlement(2025, self.TAX_2025 - 3.50, paid=1100.0, children=1)
        self.assertEqual(rz.tax_underpayment_waived, 0.0)
        self.assertEqual(rz.result_amount, 96.50)
        self.assertEqual(rz.result_type, "preplatok")

    def test_small_underpayment_over_the_bonus_due_is_dropped(self):
        """2,00 of bonus due against 4,00: 2,00 set off, the rest not withheld."""
        rz = self._settlement(2025, self.TAX_2025 - 4.00, paid=1198.0, children=1)
        self.assertEqual(rz.tax_underpayment_waived, 2.00)
        self.assertEqual(rz.result_amount, 0.0)
        assigned = self._settlement(
            2025, self.TAX_2025 - 4.00, paid=1198.0, children=1,
            assigns_tax_share=True)
        self.assertEqual(assigned.result_amount, -2.00)

    def test_bonus_taken_back_is_not_a_small_underpayment(self):
        """The 3,50 of tax is not withheld; the 100 of bonus still is."""
        rz = self._settlement(2025, self.TAX_2025 - 3.50, paid=1300.0, children=1)
        self.assertEqual(rz.tax_underpayment_waived, 3.50)
        self.assertEqual(rz.result_amount, -100.0)

    def test_small_overpayment_is_returned(self):
        rz = self._settlement(2025, self.TAX_2025 + 3.50)
        self.assertEqual(rz.tax_underpayment_waived, 0.0)
        self.assertEqual(rz.result_amount, 3.50)
        self.assertEqual(rz.result_type, "preplatok")

    def test_underpayment_limit_is_a_dated_parameter(self):
        code = "l10n_sk_tax_underpayment_not_withheld"
        for day in (date(2023, 1, 1), date(2025, 12, 31), date(2027, 1, 1)):
            with self.subTest(day=day):
                self.assertEqual(self._parameter(code, day), 5.0)
