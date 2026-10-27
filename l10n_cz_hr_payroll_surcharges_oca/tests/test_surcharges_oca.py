# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech surcharges as they land on an OCA-engine payslip.

Figures are hand-derived from the statute and the shipped rate data, not read
back off the rules under test.
"""

from datetime import date

from odoo.tests import TransactionCase, tagged

MOD = "l10n_cz_hr_payroll_surcharges"


@tagged("post_install", "-at_install")
class TestCzPriplatkyOca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "CZ Priplatky Co", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(cls.env.context,
                                       allowed_company_ids=cls.company.ids))
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Příplatkový Zaměstnanec", "company_id": cls.company.id}
        )
        # On 19.0 the contract IS hr.version, reached through the employee;
        # the OCA engine merely kept the field name contract_id for it.
        cls.contract = cls.employee.version_id
        cls.contract.write(
            {
                "date_version": date(2026, 1, 1),
                "contract_date_start": date(2026, 1, 1),
                "wage": 50000.0,
            }
        )

    def _payslip(self, inputs=None):
        vals = {
            "name": "Test",
            "employee_id": self.employee.id,
            "contract_id": self.contract.id,
            "company_id": self.company.id,
            "date_from": date(2026, 6, 1),
            "date_to": date(2026, 6, 30),
        }
        if inputs:
            vals["input_line_ids"] = [
                (0, 0, {
                    "name": code,
                    "code": code,
                    "amount": hours,
                    "contract_id": self.contract.id,
                })
                for code, hours in inputs.items()
            ]
        return self.env["hr.payslip"].create(vals)

    def test_the_mixin_is_on_the_oca_payslip(self):
        # Not hr.payslip's _inherit: that is the LAST extension's list, so with
        # the Slovak bridge installed too it names only the Slovak mixin.
        self.assertIn("hr.payslip",
                      self.env["cz.surcharge.payslip.mixin"]._inherit_children)

    def test_work100_is_gross_on_this_engine(self):
        """The OCA engine leaves absences inside WORK100; the mixin defaults
        to False and this bridge must flip it, or absences get paid twice."""
        self.assertTrue(self.env["hr.payslip"]._l10n_cz_work100_is_gross())

    def test_hours_are_read_off_the_inputs(self):
        slip = self._payslip({"NOCNI": 12.0, "PRESCAS": 5.0})
        self.assertEqual(slip._l10n_cz_surcharge_hours("NOCNI"), 12.0)
        self.assertEqual(slip._l10n_cz_surcharge_hours("PRESCAS"), 5.0)
        self.assertEqual(slip._l10n_cz_surcharge_hours("VIKEND"), 0.0)

    def test_the_five_rules_are_installed(self):
        for code in ("PRESCAS", "SVATEK", "NOCNI", "VIKEND", "ZTIZENE"):
            rule = self.env["hr.salary.rule"].search(
                [("code", "=", "PRIPLATEK_" + code)], limit=1
            )
            self.assertTrue(rule, "missing salary rule for %s" % code)

    def test_the_five_rules_are_on_the_czech_structure(self):
        structure = self.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        codes = set(structure.rule_ids.mapped("code"))
        for code in ("PRESCAS", "SVATEK", "NOCNI", "VIKEND", "ZTIZENE"):
            self.assertIn("PRIPLATEK_" + code, codes)

    def test_a_czech_payslip_pays_the_surcharge(self):
        """End to end: a CZMONTHLY payslip with night hours carries the
        surcharge line, and the surcharge reaches GROSS. Before the rules were
        attached to the structure this produced no line at all."""
        structure = self.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        slip = self._payslip({"NOCNI": 10.0})
        slip.struct_id = structure
        slip.compute_sheet()
        lines = {line.code: line.total for line in slip.line_ids}
        expected = slip._l10n_cz_surcharge_amount("NOCNI")
        self.assertGreater(expected, 0.0)
        self.assertAlmostEqual(lines.get("PRIPLATEK_NOCNI", 0.0), expected, 2)
        self.assertAlmostEqual(
            lines["GROSS"], lines["BASIC"] + expected, 2,
            "The surcharge is part of the gross wage.")

    def test_part_time_difficult_environment_uses_the_employer_week(self):
        """§ 111 odst. 5 raises the hourly minimum wage only for a shorter
        STANOVENÁ týdenní pracovní doba (the employer's full-time week), not
        for an individually shorter one (§ 80). A 20 h/week part-timer at a
        40 h company is paid on the ordinary 134.40, so 8 h x 134.40 x 10 %
        x 2 influences = 215.04 — not 430.08 on a doubled hourly figure."""
        full = self.env["resource.calendar"].create(
            {"name": "CZ 40h", "company_id": self.company.id})
        part = self.env["resource.calendar"].create({
            "name": "CZ 20h",
            "company_id": self.company.id,
            "hours_per_day": 4.0,
            "attendance_ids": [
                (0, 0, {"name": "d%s" % d, "dayofweek": str(d),
                        "hour_from": 8.0, "hour_to": 12.0,
                        "day_period": "morning"})
                for d in range(5)
            ],
        })
        self.assertAlmostEqual(part.hours_per_week, 20.0, places=2)
        self.company.resource_calendar_id = full
        self.employee.version_id.write({
            "resource_calendar_id": part.id,
            "l10n_cz_difficult_factors": 2,
        })
        slip = self._payslip({"ZTIZENE": 8.0})
        self.assertAlmostEqual(slip._l10n_cz_min_wage_hourly(), 134.40, places=2)
        self.assertAlmostEqual(
            slip._l10n_cz_surcharge_amount("ZTIZENE"), 215.04, places=2
        )

    def test_difficult_environment_needs_a_factor_count(self):
        """§ 117 pays per aggravating influence, so hours alone must not pay.

        This is the trap the Slovak module does not have: there, difficult
        work is a percentage with no multiplier. Here a contract that records
        difficult hours but no influences owes nothing.
        """
        slip = self._payslip({"ZTIZENE": 8.0})
        self.assertEqual(slip._l10n_cz_surcharge_hours("ZTIZENE"), 8.0)
        self.assertEqual(slip._l10n_cz_difficult_factors(), 0)
        self.assertEqual(slip._l10n_cz_surcharge_amount("ZTIZENE"), 0.0)

    # ------------------------------------------------------------------
    # § 114 odst. 1 (overtime wage) and § 111 odst. 2 (doplatek)
    # ------------------------------------------------------------------
    def _lines(self, slip):
        slip.struct_id = self.env.ref(
            "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary")
        slip.compute_sheet()
        return {line.code: line.total for line in slip.line_ids}

    def _low_paid_slip(self, wage, inputs=None, **vals):
        employee = self.env["hr.employee"].create(
            {"name": "Minimální Mzda", "company_id": self.company.id})
        contract = employee.version_id
        contract.write(dict(
            {"date_version": date(2026, 1, 1),
             "contract_date_start": date(2026, 1, 1),
             "wage": wage}, **vals))
        saved = (self.employee, self.contract)
        self.employee, self.contract = employee, contract
        try:
            return self._payslip(inputs)
        finally:
            self.employee, self.contract = saved

    def test_overtime_hours_are_paid_their_wage_and_the_surcharge(self):
        """§ 114 odst. 1: "mzda ... a příplatek". 10 overtime hours at
        50000 / 176 h (June 2026) = 2840.91 of dosažená mzda."""
        r = self._lines(self._payslip({"PRESCAS": 10.0}))
        self.assertAlmostEqual(r["MZDA_PRESCAS"], 2840.91, places=2)
        self.assertGreater(r["PRIPLATEK_PRESCAS"], 0.0)
        self.assertAlmostEqual(
            r["GROSS"],
            r["BASIC"] + r["MZDA_PRESCAS"] + r["PRIPLATEK_PRESCAS"], places=2)

    def test_minimum_wage_top_up_on_the_hourly_basis(self):
        """§ 111 odst. 2 písm. a): 176 h x 134.40 - 15000 = 8654.40."""
        r = self._lines(self._low_paid_slip(15000.0))
        self.assertAlmostEqual(r["MINWAGE_TOPUP"], 8654.40, places=2)
        self.assertAlmostEqual(r["GROSS"], 23654.40, places=2)

    def test_minimum_wage_top_up_on_an_agreed_monthly_basis(self):
        r = self._lines(self._low_paid_slip(
            15000.0, l10n_cz_min_wage_basis="monthly"))
        self.assertAlmostEqual(r["MINWAGE_TOPUP"], 7400.0, places=2)

    def test_minimum_wage_top_up_ignores_surcharges(self):
        r = self._lines(self._low_paid_slip(15000.0, {"NOCNI": 20.0}))
        self.assertGreater(r["PRIPLATEK_NOCNI"], 0.0)
        self.assertAlmostEqual(r["MINWAGE_TOPUP"], 8654.40, places=2)

    def test_no_top_up_above_the_minimum_wage(self):
        r = self._lines(self._payslip())
        self.assertNotIn("MINWAGE_TOPUP", r)
