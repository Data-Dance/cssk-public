# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A confirmed payslip is not computed again."""

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkConfirmedPayslip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK Confirmed Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Confirmed", "company_id": cls.company.id}
        )
        cls.contract = cls.employee.version_id
        cls.contract.write(
            {
                "contract_date_start": date(2024, 1, 1),
                "date_version": date(2024, 1, 1),
                "wage": 1500.0,
                "struct_id": cls.structure.id,
            }
        )

    def _slip(self):
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "June",
                    "employee_id": self.employee.id,
                    "contract_id": self.contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        slip.compute_sheet()
        return slip

    @staticmethod
    def _snapshot(slip):
        return (
            slip.state,
            sorted(slip.line_ids.ids),
            sorted((line.code, line.total) for line in slip.line_ids),
            slip.l10n_sk_fund_assessment,
        )

    def test_compute_sheet_leaves_a_confirmed_payslip_as_it_is(self):
        slip = self._slip()
        slip.action_payslip_done()
        self.assertEqual(slip.state, "done")
        self.assertEqual(slip.get_salary_line_total("GROSS"), 1500.0)
        self.assertTrue(slip.l10n_sk_fund_assessment)
        before = self._snapshot(slip)
        self.contract.wage = 2000.0
        slip.compute_sheet()
        self.assertEqual(self._snapshot(slip), before)

    def test_confirming_a_confirmed_payslip_again_changes_nothing(self):
        slip = self._slip()
        slip.action_payslip_done()
        before = self._snapshot(slip)
        self.contract.wage = 2000.0
        slip.action_payslip_done()
        self.assertEqual(self._snapshot(slip), before)

    def test_compute_sheet_leaves_a_cancelled_payslip_as_it_is(self):
        slip = self._slip()
        slip.state = "cancel"
        before = self._snapshot(slip)
        self.contract.wage = 2000.0
        slip.compute_sheet()
        self.assertEqual(self._snapshot(slip), before)

    def test_draft_and_waiting_payslips_are_computed(self):
        slip = self._slip()
        self.assertEqual(slip.state, "verify")
        self.contract.wage = 2000.0
        slip.compute_sheet()
        self.assertEqual(slip.get_salary_line_total("GROSS"), 2000.0)
        slip.action_payslip_done()
        self.assertEqual(slip.state, "done")
        self.assertEqual(slip.get_salary_line_total("GROSS"), 2000.0)

    def test_a_batch_computes_only_what_is_open(self):
        confirmed = self._slip()
        confirmed.action_payslip_done()
        before = self._snapshot(confirmed)
        waiting = self._slip()
        self.contract.wage = 2000.0
        (confirmed | waiting).compute_sheet()
        self.assertEqual(self._snapshot(confirmed), before)
        self.assertEqual(waiting.get_salary_line_total("GROSS"), 2000.0)
