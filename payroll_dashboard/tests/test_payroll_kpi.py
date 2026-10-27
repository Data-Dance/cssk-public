# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPayrollKpi(TransactionCase):
    """The tiles are per company, count only done payslips, and find the
    totals of both the Slovak and the Czech rule sets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "KPI Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "KPI Co B"})
        cls.category = cls.env["hr.salary.rule.category"].create(
            {"name": "KPI test", "code": "KPITEST"}
        )
        # Created once here: a rule made inside one test is rolled back with
        # it, so a lazily filled cache would point the next test at nothing.
        cls.rules = {
            code: cls.env["hr.salary.rule"].create(
                {"name": code, "code": code, "category_id": cls.category.id}
            )
            for code in (
                "GROSS", "NET", "SOCIALEMPLOYERTOTAL", "INCOMETAXTOTAL",
                "SOCIALERTOT", "HEALTHERTOT", "SOCIAL_DISCOUNT", "INCOMETAXTOT",
            )
        }

    @classmethod
    def _rule(cls, code):
        return cls.rules[code]

    @classmethod
    def _slip(cls, company, state, lines, name="Emp"):
        employee = cls.env["hr.employee"].create(
            {"name": name, "company_id": company.id}
        )
        slip = cls.env["hr.payslip"].create(
            {
                "employee_id": employee.id,
                "contract_id": employee.version_id.id,
                "company_id": company.id,
                "date_from": date(2026, 6, 1),
                "date_to": date(2026, 6, 30),
            }
        )
        for code, amount in lines.items():
            rule = cls._rule(code)
            cls.env["hr.payslip.line"].create(
                {
                    "slip_id": slip.id,
                    "salary_rule_id": rule.id,
                    "employee_id": employee.id,
                    "contract_id": employee.version_id.id,
                    "name": code,
                    "code": code,
                    "category_id": cls.category.id,
                    "amount": amount,
                }
            )
        slip.state = state
        return slip

    def _tiles(self, company, env=None):
        env = env or self.env
        # The tiles are a SQL view: pending ORM writes must reach the tables.
        env.flush_all()
        env["payroll.kpi"].invalidate_model()
        records = env["payroll.kpi"].search([("company_id", "=", company.id)])
        return {r.kpi: r.value for r in records}

    def test_per_company_done_only_both_rule_sets(self):
        # Company A: a Slovak done slip, plus a draft and a cancelled one.
        self._slip(self.company_a, "done", {
            "GROSS": 1000.0, "NET": 700.0,
            "SOCIALEMPLOYERTOTAL": 352.0, "INCOMETAXTOTAL": 80.0,
        })
        self._slip(self.company_a, "draft", {"GROSS": 5000.0, "NET": 4000.0})
        self._slip(self.company_a, "cancel", {"GROSS": 7000.0})
        # Company B: a Czech done slip.
        self._slip(self.company_b, "done", {
            "GROSS": 2000.0, "NET": 1500.0, "SOCIALERTOT": 496.0,
            "HEALTHERTOT": 180.0, "SOCIAL_DISCOUNT": -100.0,
            "INCOMETAXTOT": 150.0,
        })
        a = self._tiles(self.company_a)
        self.assertEqual(a["gross"], 1000.0, "draft/cancelled slips excluded")
        self.assertEqual(a["net"], 700.0)
        self.assertEqual(a["employer"], 352.0)
        self.assertEqual(a["labour_cost"], 1352.0)
        self.assertEqual(a["income_tax"], 80.0)
        self.assertEqual(a["payslips"], 1)
        self.assertEqual(a["employees"], 1)
        b = self._tiles(self.company_b)
        self.assertEqual(b["gross"], 2000.0, "not mixed with company A")
        self.assertEqual(b["employer"], 576.0, "CZ social + health - discount")
        self.assertEqual(b["labour_cost"], 2576.0)
        self.assertEqual(b["income_tax"], 150.0)

    def test_other_company_invisible(self):
        self._slip(self.company_b, "done", {"GROSS": 2000.0})
        user = self.env["res.users"].create({
            "name": "KPI viewer", "login": "kpi_viewer",
            "company_id": self.company_a.id,
            "company_ids": [(6, 0, [self.company_a.id])],
            "group_ids": [(6, 0, [self.env.ref("payroll.group_payroll_user").id])],
        })
        env = self.env(user=user, context={"allowed_company_ids": [self.company_a.id]})
        env.flush_all()
        tiles = env["payroll.kpi"].search([])
        self.assertTrue(tiles)
        self.assertEqual(tiles.company_id, self.company_a)

    def test_tile_names_are_translatable_selection(self):
        field = self.env["payroll.kpi"]._fields["kpi"]
        self.assertEqual(field.type, "selection")
        self.assertIn(("gross", "Total gross"), field.selection)
