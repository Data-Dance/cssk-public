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

    def _split_insurer_accounts(self):
        """Keep the two actual creditors on distinct company accounts."""
        social = self._account("336000").copy(
            {"code": "336100", "name": "Social insurance settlement"}
        )
        health = self._account("336000").copy(
            {"code": "336250", "name": "Health insurance settlement"}
        )
        from ..models.account_chart_template import _sk_full_mapping

        configured = self.env["hr.salary.rule"]
        for xmlid, sides in _sk_full_mapping().items():
            rule = self.env.ref(xmlid, raise_if_not_found=False)
            if not rule or "336000" not in sides.values():
                continue
            account = health if "health" in xmlid else social
            values = {
                "account_" + side: account.id
                for side, code in sides.items()
                if code == "336000"
            }
            rule.with_company(self.company).write(values)
            configured |= rule
        return configured.with_company(self.company), social, health

    def test_repeated_mapping_preserves_custom_insurer_accounts(self):
        rules, social, health = self._split_insurer_accounts()
        before = {
            rule.id: (rule.account_debit.id, rule.account_credit.id) for rule in rules
        }
        self.env["account.chart.template"]._configure_sk_payroll_accounts(self.company)
        self.assertEqual(
            {
                rule.id: (rule.account_debit.id, rule.account_credit.id)
                for rule in rules
            },
            before,
            "Repeated chart setup must preserve the user's insurer analytics",
        )
        self.assertEqual(social.company_ids, self.company)
        self.assertEqual(health.company_ids, self.company)

    def test_chart_reload_retains_split_insurer_posting(self):
        rules, social, health = self._split_insurer_accounts()
        before = {
            rule.id: (rule.account_debit.id, rule.account_credit.id) for rule in rules
        }
        self.env["account.chart.template"].try_loading(
            "sk", company=self.company, install_demo=False
        )
        self.assertEqual(
            {
                rule.id: (rule.account_debit.id, rule.account_credit.id)
                for rule in rules
            },
            before,
        )
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
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
        slip.compute_sheet()
        slip.action_payslip_done()
        self.assertEqual(slip.move_id.state, "posted")
        amounts = {
            account.id: sum(
                slip.move_id.line_ids.filtered(
                    lambda line, target=account: line.account_id == target
                ).mapped("balance")
            )
            for account in social | health | self._account("336000")
        }
        self.assertAlmostEqual(amounts[social.id], -519.0, places=2)
        self.assertAlmostEqual(amounts[health.id], -240.0, places=2)
        self.assertAlmostEqual(amounts[self._account("336000").id], 0.0, places=2)

    def test_existing_opposite_side_is_not_augmented_on_reload(self):
        rule = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_income_tax_employee"
        ).with_company(self.company)
        chosen = self._account("342000")
        rule.write({"account_debit": False, "account_credit": chosen.id})
        self.env["account.chart.template"]._configure_sk_payroll_accounts(self.company)
        self.assertFalse(rule.account_debit)
        self.assertEqual(rule.account_credit, chosen)

    def test_explicitly_cleared_pair_receives_default_mapping(self):
        rules, _social, _health = self._split_insurer_accounts()
        rule = rules.filtered(lambda item: item.code == "HEALTH").ensure_one()
        rule.write({"account_debit": False, "account_credit": False})
        self.env["account.chart.template"]._configure_sk_payroll_accounts(self.company)
        self.assertEqual(rule.account_debit, self._account("336000"))
        self.assertFalse(rule.account_credit)

    def test_foreign_company_fallback_is_replaced_without_touching_other_company(self):
        rule = self.env.ref(
            "l10n_sk_hr_payroll_oca."
            "l10n_sk_hr_payroll_structure_sk_employee_salary_basic_salary_rule"
        ).with_company(self.company)
        chosen = self._account("527000")
        rule.account_debit = chosen
        other_company = self.env["res.company"].create(
            {
                "name": "Second SK payroll company",
                "country_id": self.env.ref("base.sk").id,
            }
        )
        self.env.user.company_ids |= other_company
        self.env["account.chart.template"].try_loading(
            "sk", company=other_company, install_demo=False
        )
        other_rule = rule.with_company(other_company)
        other_rule.write({"account_debit": chosen.id, "account_credit": chosen.id})
        self.env["account.chart.template"]._configure_sk_payroll_accounts(other_company)
        self.assertEqual(other_rule.account_debit.code, "521000")
        self.assertIn(other_company, other_rule.account_debit.company_ids)
        self.assertFalse(other_rule.account_credit)
        self.assertEqual(rule.account_debit, chosen)
        # A partially configured pair must not preserve its foreign side merely
        # because the other side is already valid for this company.
        local_debit = other_rule.account_debit
        other_rule.account_credit = chosen
        self.env["account.chart.template"]._configure_sk_payroll_accounts(other_company)
        self.assertEqual(other_rule.account_debit, local_debit)
        self.assertFalse(other_rule.account_credit)
        self.assertEqual(rule.account_debit, chosen)

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
            line.debit for line in move.line_ids if line.account_id.code == "521000"
        )
        self.assertAlmostEqual(wage_debit, 1500.0, places=2)

        # Net pay credit (331) equals the payslip NET line.
        net_total = payslip.get_salary_line_total("NET")
        net_credit = sum(
            line.credit for line in move.line_ids if line.account_id.code == "331000"
        )
        self.assertAlmostEqual(net_credit, net_total, places=2)

    # Rules that carry a total or an informational figure, never money of
    # their own. Anything else that ends on a payslip must reach an account,
    # or payroll_account books it into the journal's adjustment line.
    INFORMATIONAL = {
        "GROSS",
        "TAXBASE",
        "OOP_PENSION",
        "SOCIALEMPLOYEETOTAL",
        "SOCIALEMPLOYERTOTAL",
        "INCOMETAXTOTAL",
    }

    def _sk_rules(self):
        data = self.env["ir.model.data"].search(
            [
                ("model", "=", "hr.salary.rule"),
                (
                    "module",
                    "in",
                    ("l10n_sk_hr_payroll_oca", "l10n_sk_hr_payroll_surcharges_oca"),
                ),
            ]
        )
        return (
            self.env["hr.salary.rule"]
            .browse(data.mapped("res_id"))
            .with_company(self.company)
        )

    def test_every_money_rule_maps_to_an_account(self):
        """ANNUAL_TAX_SETTLEMENT, PREKAZKA_NAHRADA and the surcharges used to
        have no account at all."""
        unmapped = self._sk_rules().filtered(
            lambda r: r.code not in self.INFORMATIONAL
            and not (r.account_debit or r.account_credit)
        )
        self.assertFalse(sorted(unmapped.mapped("code")))
        settlement = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_annual_tax_settlement"
        ).with_company(self.company)
        self.assertEqual(settlement.account_debit.code, "342000")
        obstacle = self.env.ref(
            "l10n_sk_hr_payroll_oca.l10n_sk_employer_obstacle_allowance"
        ).with_company(self.company)
        self.assertEqual(obstacle.account_debit.code, "521000")

    def test_surcharges_installed_later_are_mapped_alone(self):
        """The surcharges hook maps its own rules and nothing else."""
        night = self.env.ref(
            "l10n_sk_hr_payroll_surcharges_oca.l10n_sk_priplatok_noc",
            raise_if_not_found=False,
        )
        if not night:
            self.skipTest("l10n_sk_hr_payroll_surcharges_oca not installed")
        night = night.with_company(self.company)
        basic = self.env.ref(
            "l10n_sk_hr_payroll_oca."
            "l10n_sk_hr_payroll_structure_sk_employee_salary_basic_salary_rule"
        ).with_company(self.company)
        other = self._account("527000")
        basic.account_debit = other  # a user's own choice since the install
        night.account_debit = False  # as if installed after the bridge
        self.env["account.chart.template"]._l10n_sk_payroll_map_rules(
            "l10n_sk_hr_payroll_surcharges_oca"
        )
        self.assertEqual(night.account_debit.code, "521000")
        self.assertEqual(basic.account_debit, other)


@tagged("post_install", "-at_install")
class TestSkChartLoadedWithoutPayrollRights(TransactionCase):
    def test_accounting_admin_without_payroll_rights_loads_the_chart(self):
        """Loading the Slovak chart maps the salary rules even when the user
        doing it holds no payroll rights (an accounting manager / settings
        admin, as when a new company is set up). OCA payroll grants such a
        user no write on salary rules; the mapping used to raise AccessError
        and abort the chart load."""
        from odoo.tests import new_test_user

        company = self.env["res.company"].create(
            {"name": "SK No Payroll Co", "country_id": self.env.ref("base.sk").id}
        )
        user = new_test_user(
            self.env,
            login="sk_acct_no_payroll",
            groups="base.group_user,base.group_system,account.group_account_manager",
            company_id=company.id,
            company_ids=[(6, 0, company.ids)],
        )
        rule = self.env.ref("l10n_sk_hr_payroll_oca.l10n_sk_income_tax_employee")
        self.assertFalse(rule.with_user(user).has_access("write"))
        self.env["account.chart.template"].with_user(user).try_loading(
            "sk", company=company, install_demo=False
        )
        self.assertTrue(rule.with_company(company).account_debit)
