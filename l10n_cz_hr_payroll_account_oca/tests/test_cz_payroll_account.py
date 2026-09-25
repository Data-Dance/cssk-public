# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Posts a Czech payslip through the OCA payroll engine to the general ledger
# and asserts the resulting account.move exists and is balanced. In 19.0 the
# "contract" is the employee's working version (hr.version).

from datetime import date

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_cz_hr_payroll_account_oca.hooks import (
    _configure_cz_payroll_accounts,
)


@tagged("post_install", "-at_install")
class TestCzPayrollAccount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Acct Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))

        cls.env["account.chart.template"].try_loading(
            "cz", company=cls.company, install_demo=False)
        _configure_cz_payroll_accounts(cls.env, cls.company)

        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.structure = cls.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        cls.journal = cls.env["account.journal"].search(
            [("code", "=", "SLR"), ("company_id", "=", cls.company.id)], limit=1)

    def _account(self, code):
        return self.env["account.account"].with_company(self.company).search([
            *self.env["account.account"]._check_company_domain(self.company),
            ("code", "=like", "%s%%" % code),
        ], limit=1)

    def test_post_payslip_balanced(self):
        self.assertTrue(self.journal, "Hook did not create the Salaries journal")

        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "CZ Emp",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": 50000.0,
            "struct_id": self.structure.id,
        })
        version = employee.version_id
        version.write({
            "journal_id": self.journal.id,
            "l10n_cz_tax_declaration": True,
        })

        gross_rule = self.env.ref("l10n_cz_hr_payroll_oca.cz_gross_salary_rule")
        self.assertTrue(gross_rule.with_company(self.company).account_debit)
        self.assertTrue(gross_rule.with_company(self.company).account_credit)

        payslip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip CZ",
            "employee_id": employee.id,
            "contract_id": version.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
        })
        payslip.compute_sheet()
        gross = sum(payslip.line_ids.filtered(lambda l: l.code == "GROSS").mapped("total"))
        self.assertAlmostEqual(gross, 50000.0, 2)

        payslip.action_payslip_done()

        move = payslip.move_id
        self.assertTrue(move, "No accounting entry created for the payslip")

        debit = sum(move.line_ids.mapped("debit"))
        credit = sum(move.line_ids.mapped("credit"))
        self.assertAlmostEqual(debit, credit, 2, "Payslip journal entry is not balanced")
        self.assertGreater(debit, 0.0, "Empty journal entry")

        accounts = set(move.line_ids.mapped("account_id"))
        for code in ("521", "331", "336", "342", "524"):
            self.assertIn(
                self._account(code), accounts,
                "Expected account %s missing from the payslip move" % code)

        self.assertFalse(
            move.line_ids.filtered(lambda l: l.name == "Adjustment Entry"),
            "An adjustment line was needed -> mapping is not self-balancing")

        net = sum(payslip.line_ids.filtered(lambda l: l.code == "NET").mapped("total"))
        acc_331 = self._account("331")
        lines_331 = move.line_ids.filtered(lambda l: l.account_id == acc_331)
        residual = sum(lines_331.mapped("credit")) - sum(lines_331.mapped("debit"))
        self.assertAlmostEqual(residual, net, 2,
            "Net residual on 331 does not match NET")
