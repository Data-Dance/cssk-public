# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Posts a Czech payslip through the OCA payroll engine to the general ledger
# and asserts the resulting account.move exists and is balanced. In 19.0 the
# "contract" is the employee's working version (hr.version).

from datetime import date

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_cz_hr_payroll_account_oca.hooks import (
    RULE_ACCOUNT_MAP,
    _configure_cz_payroll_accounts,
    _cz_rules_by_code,
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

    def test_every_mapping_key_resolves(self):
        """Every code in the map is a rule of the Czech structure and got both
        accounts. A key that resolves to nothing would be skipped silently."""
        rules, missing = _cz_rules_by_code(self.env)
        self.assertFalse(missing, "Unresolved CZ payroll rule codes: %s" % missing)
        for code in RULE_ACCOUNT_MAP:
            rule = rules[code].with_company(self.company)
            self.assertTrue(rule.account_debit, "%s has no debit account" % code)
            self.assertTrue(rule.account_credit, "%s has no credit account" % code)

    def test_child_bonus_settlement_and_discount_are_posted(self):
        """Daňový bonus, the annual-settlement refund and the employer discount
        all move money. Unmapped, the employee was paid them but 331 never
        carried them, so 331 no longer matched NET."""
        employee = self.env["hr.employee"].with_company(self.company).create({
            "name": "CZ Emp Bonus",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": 25000.0,
            "struct_id": self.structure.id,
        })
        version = employee.version_id
        version.write({
            "journal_id": self.journal.id,
            "l10n_cz_tax_declaration": True,
            "l10n_cz_children_t1": 1,
            "l10n_cz_children_t2": 1,
            "l10n_cz_children_t3": 1,
            "l10n_cz_social_discount_category": "under21",
        })
        payslip = self.env["hr.payslip"].with_company(self.company).create({
            "name": "Payslip CZ bonus",
            "employee_id": employee.id,
            "contract_id": version.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date(2026, 3, 1),
            "date_to": date(2026, 3, 31),
            "input_line_ids": [(0, 0, {
                "name": "Annual Tax Reconciliation",
                "code": "ANNUAL_TAX_SETTLEMENT",
                "amount": 1500.0,
                "contract_id": version.id,
            })],
        })
        payslip.compute_sheet()
        totals = {line.code: line.total for line in payslip.line_ids}
        for code in ("CHILDBONUS", "ANNUAL_TAX_SETTLEMENT", "SOCIAL_DISCOUNT"):
            self.assertTrue(totals.get(code), "%s not on the payslip" % code)

        payslip.action_payslip_done()
        move = payslip.move_id
        self.assertAlmostEqual(
            sum(move.line_ids.mapped("debit")),
            sum(move.line_ids.mapped("credit")), 2)
        self.assertFalse(
            move.line_ids.filtered(lambda l: l.name == "Adjustment Entry"))

        def balance(code):
            lines = move.line_ids.filtered(
                lambda l: l.account_id == self._account(code))
            return sum(lines.mapped("credit")) - sum(lines.mapped("debit"))

        self.assertAlmostEqual(balance("331"), totals["NET"], 2,
            "331 must carry the whole net pay, bonus and refund included")
        # 342: advance less credits, less the bonus and the refund paid out.
        tax_payable = (-totals.get("INCOMETAX", 0.0) - totals.get("TAXCREDIT", 0.0)
                       - totals.get("CHILDBEN", 0.0) - totals["CHILDBONUS"]
                       - totals["ANNUAL_TAX_SETTLEMENT"])
        self.assertAlmostEqual(balance("342"), tax_payable, 2)
        # 524 expense is the gross premium less the discount.
        employer_si = (totals.get("SOCIALER", 0.0) + totals.get("HEALTHER", 0.0)
                       + totals["SOCIAL_DISCOUNT"])
        self.assertAlmostEqual(-balance("524"), employer_si, 2)

    def test_company_loading_the_chart_later_is_configured(self):
        """The install hook only reached companies already on the Czech chart.
        A company that loads it afterwards must get the accounts and the
        Salaries journal too, without calling the hook by hand."""
        company = self.env["res.company"].create(
            {"name": "CZ Later Co", "country_id": self.env.ref("base.cz").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].with_context(
            allowed_company_ids=company.ids).try_loading(
            "cz", company=company, install_demo=False)
        gross_rule = self.env.ref("l10n_cz_hr_payroll_oca.cz_gross_salary_rule")
        debit = gross_rule.with_company(company).account_debit
        self.assertTrue(debit)
        self.assertIn(company, debit.company_ids)
        self.assertTrue(debit.with_company(company).code.startswith("521"))
        self.assertTrue(self.env["account.journal"].search(
            [("code", "=", "SLR"), ("company_id", "=", company.id)]))


@tagged("post_install", "-at_install")
class TestCzChartLoadedWithoutPayrollRights(TransactionCase):
    def test_accounting_admin_without_payroll_rights_loads_the_chart(self):
        """Loading the Czech chart maps the salary rules even when the user
        doing it holds no payroll rights. OCA payroll grants an accounting
        manager / settings admin no write on salary rules; the mapping used
        to raise AccessError and abort the chart load."""
        from odoo.tests import new_test_user

        company = self.env["res.company"].create(
            {"name": "CZ No Payroll Co", "country_id": self.env.ref("base.cz").id}
        )
        user = new_test_user(
            self.env,
            login="cz_acct_no_payroll",
            groups="base.group_user,base.group_system,account.group_account_manager",
            company_id=company.id,
            company_ids=[(6, 0, company.ids)],
        )
        rule = _cz_rules_by_code(self.env)[0]["GROSS"]
        self.assertFalse(rule.with_user(user).has_access("write"))
        self.env["account.chart.template"].with_user(user).try_loading(
            "cz", company=company, install_demo=False
        )
        self.assertTrue(rule.with_company(company).account_debit)
