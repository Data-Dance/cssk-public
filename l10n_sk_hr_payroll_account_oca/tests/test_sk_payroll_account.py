# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Runtime proof that a posted Slovak payslip produces a balanced journal entry
# on the expected l10n_sk accounts (521 / 331 / 336 / 342 / 524).
#
# On 19.0 the payslip ``contract_id`` is an ``hr.version`` record owned by the
# employee; the salary journal (from payroll_account) lives on that version.

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkPayrollAccount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK Acct Co",
                "country_id": cls.env.ref("base.sk").id,
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        # Load the Slovak chart -> triggers _configure_sk_payroll_accounts.
        cls.env["account.chart.template"].try_loading(
            "sk", company=cls.company, install_demo=False
        )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Salary Journal",
                "code": "SLR",
                "type": "general",
                "company_id": cls.company.id,
                "default_account_id": cls._account("521000").id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Jozef Uctovnik",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )
        # On 19.0 the "contract" is the employee's current version.
        cls.contract = cls.employee.version_id
        cls.contract.write(
            {
                "contract_date_start": date(2024, 1, 1),
                "date_version": date(2024, 1, 1),
                "wage": 1500.0,
                "resource_calendar_id": cls.calendar.id,
                "struct_id": cls.structure.id,
                "journal_id": cls.journal.id,
                "l10n_sk_tax_declaration_signed": True,
            }
        )

    @classmethod
    def _account(cls, code):
        return (
            cls.env["account.account"]
            .with_company(cls.company)
            .search([("code", "=", code)], limit=1)
        )

    def test_mapping_resolved_on_rules(self):
        """The company-dependent debit/credit accounts are set on the rules."""
        basic = self.env.ref(
            "l10n_sk_hr_payroll_oca."
            "l10n_sk_hr_payroll_structure_sk_employee_salary_basic_salary_rule"
        ).with_company(self.company)
        net = self.env.ref(
            "l10n_sk_hr_payroll_oca."
            "l10n_sk_hr_payroll_structure_sk_employee_salary_net_salary"
        ).with_company(self.company)
        self.assertEqual(basic.account_debit.code, "521000")
        self.assertEqual(net.account_credit.code, "331000")

    def test_posted_payslip_is_balanced(self):
        payslip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "June 2026",
                    "employee_id": self.employee.id,
                    "contract_id": self.contract.id,
                    "struct_id": self.structure.id,
                    "company_id": self.company.id,
                    "journal_id": self.journal.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        payslip.compute_sheet()
        payslip.action_payslip_done()

        move = payslip.move_id
        self.assertTrue(move, "Posting the payslip must create an account.move")
        self.assertEqual(move.state, "posted")

        debit = sum(move.line_ids.mapped("debit"))
        credit = sum(move.line_ids.mapped("credit"))
        self.assertAlmostEqual(debit, credit, places=2)
        self.assertGreater(debit, 0.0)

        # No adjustment line was needed: the entry balances on the real
        # payroll accounts only (521/331/336/342/524).
        codes = set(move.line_ids.mapped("account_id.code"))
        self.assertIn("521000", codes)  # gross wage expense (debit)
        self.assertIn("331000", codes)  # net pay payable (credit)
        self.assertIn("336000", codes)  # SP/ZP settlement (credit)
        self.assertIn("342000", codes)  # income tax withheld (credit)
        self.assertIn("524000", codes)  # employer contribution expense (debit)

        # Gross wage (521) debit equals the full monthly wage.
        wage_debit = sum(
            line.debit
            for line in move.line_ids
            if line.account_id.code == "521000"
        )
        self.assertAlmostEqual(wage_debit, 1500.0, places=2)

        # Net pay credit (331) equals the payslip NET line.
        net_total = payslip.get_salary_line_total("NET")
        net_credit = sum(
            line.credit
            for line in move.line_ids
            if line.account_id.code == "331000"
        )
        self.assertAlmostEqual(net_credit, net_total, places=2)
