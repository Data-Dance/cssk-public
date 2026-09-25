# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drive the shared Czech scenarios through whichever payroll engine is present.

The two engines cannot coexist in one database — both claim ``hr.payslip`` — so
parity cannot be asserted inside a single run. Instead this one test file is
installed in BOTH engines' databases and asserts against the SAME expected
figures in ``parity_cz.py``. Divergence therefore fails on whichever side moved.

That makes the CI contract explicit: this module must be installed in both
payroll databases and both runs must be green. One green run proves half of the
property and is not evidence of parity.
"""

from datetime import date

from odoo.addons.l10n_cz_hr_payroll_parity.parity_cz import (
    AVG_EARNINGS_SCENARIOS,
    ENGINE_EE,
    ENGINE_OCA,
    SCENARIOS,
    SEED_PERIOD,
    codes_for,
)
from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import COUNTRY_CZ
from odoo.tests import TransactionCase, tagged

OCA_STRUCT = "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"
EE_STRUCT = "l10n_cz_hr_payroll_ee.hr_payroll_structure_cz_employee_salary"


@tagged("post_install", "-at_install")
class TestCzPayrollEngineParity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.env.user.group_ids |= cls.env.ref(
            "hr_holidays.group_hr_holidays_manager"
        )
        if cls.engine == ENGINE_OCA:
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = cls.env.ref(OCA_STRUCT)
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager"
            )
            cls.structure = cls.env.ref(EE_STRUCT)
        cls.company = cls.env["res.company"].create(
            {
                "name": "CZ Parity Co",
                "country_id": cls.env.ref("base.cz").id,
                "currency_id": cls.env.ref("base.CZK").id,
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        # An explicit calendar on both sides: proration divides by the
        # calendar's hours, so leaving it implicit would compare two different
        # denominators and call the difference an engine bug.
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.company.resource_calendar_id = cls.calendar

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(OCA_STRUCT, raise_if_not_found=False):
            return ENGINE_OCA
        return ENGINE_EE

    def _module_installed(self, name):
        return bool(
            self.env["ir.module.module"].search_count(
                [("name", "=", name), ("state", "=", "installed")]
            )
        )

    # ------------------------------------------------------------------
    # engine-specific construction
    # ------------------------------------------------------------------
    def _scenario_calendar(self, scenario):
        """The shared 40 h/week calendar, unless the scenario asks for its own.

        ``calendar_hours`` maps dayofweek -> hours, so a scenario can pin a week
        that is full-time WITHOUT being the same length every day. That is the
        shape where proration by days and payment by hours stop agreeing, and it
        is where the equivalent Slovak bug lived.
        """
        hours = scenario.get("calendar_hours")
        if not hours:
            return self.calendar
        return self.env["resource.calendar"].create(
            {
                "name": "CZ Parity %s" % scenario["key"],
                "company_id": self.company.id,
                "hours_per_day": 8.0,
                "full_time_required_hours": sum(hours.values()),
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "d%s" % day,
                            "dayofweek": day,
                            "hour_from": 8.0,
                            "hour_to": 8.0 + h,
                            "day_period": "morning",
                        },
                    )
                    for day, h in sorted(hours.items())
                ],
            }
        )

    def _make_employee(self, scenario, calendar):
        vals = {
            "name": "CZ Parity %s" % scenario["key"],
            "company_id": self.company.id,
            "resource_calendar_id": calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": scenario["wage"],
        }
        if self.engine == ENGINE_OCA:
            vals["struct_id"] = self.structure.id
        else:
            vals["structure_type_id"] = self.structure.type_id.id
        employee = self.env["hr.employee"].with_company(self.company).create(vals)
        version_vals = dict(scenario["version"])
        version_vals["resource_calendar_id"] = calendar.id
        if self.engine == ENGINE_OCA:
            version_vals["struct_id"] = self.structure.id
        employee.version_id.write(version_vals)
        return employee

    def _compute(self, employee, date_from, date_to, name):
        """A REAL payslip: worked-day lines must exist or an absence scenario
        would compare two untouched full-month payslips and pass."""
        vals = {
            "name": name,
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date_from,
            "date_to": date_to,
        }
        if self.engine == ENGINE_OCA:
            vals["contract_id"] = employee.version_id.id
        else:
            vals["version_id"] = employee.version_id.id
        slip = self.env["hr.payslip"].with_company(self.company).create(vals)
        if self.engine == ENGINE_OCA:
            # The OCA engine fills worked-day lines from an onchange, which does
            # not fire on create() in a test.
            worked = slip.get_worked_day_lines(
                employee.version_id, date_from, date_to
            )
            slip.worked_days_line_ids = [(0, 0, line) for line in worked]
        slip.compute_sheet()
        return slip

    def _seed_prior_quarter(self, employee):
        """A plain worked March 2026, marked done/validated so it counts as the
        rozhodné období for a June slip."""
        (y1, m1, d1), (y2, m2, d2) = SEED_PERIOD
        seed = self._compute(
            employee, date(y1, m1, d1), date(y2, m2, d2), "CZ Parity seed"
        )
        seed.write({"state": "done" if self.engine == ENGINE_OCA else "validated"})
        return seed

    def _book_leave(self, employee, record_name, d_from, d_to):
        """Resolve a leave type by RECORD NAME against whichever localisation is
        installed, so one scenario drives both engines."""
        module = (
            "l10n_cz_hr_payroll_oca"
            if self.engine == ENGINE_OCA
            else "l10n_cz_hr_payroll_ee"
        )
        ltype = self.env.ref("%s.%s" % (module, record_name))
        leave = (
            self.env["hr.leave"]
            .with_company(self.company)
            .create(
                {
                    "name": ltype.name,
                    "employee_id": employee.id,
                    "holiday_status_id": ltype.id,
                    "request_date_from": d_from,
                    "request_date_to": d_to,
                }
            )
        )
        if leave.state != "validate":
            leave.action_approve()
        return leave

    def _build_slip(self, scenario):
        calendar = self._scenario_calendar(scenario)
        employee = self._make_employee(scenario, calendar)
        self._seed_prior_quarter(employee)
        for name, d_from, d_to in scenario.get("leaves", ()):
            self._book_leave(employee, name, date(*d_from), date(*d_to))
        (y1, m1, d1), (y2, m2, d2) = scenario["period"]
        return self._compute(
            employee, date(y1, m1, d1), date(y2, m2, d2),
            "CZ Parity %s" % scenario["key"],
        )

    @staticmethod
    def _totals(slip):
        totals = {}
        for line in slip.line_ids:
            totals[line.code] = totals.get(line.code, 0.0) + line.total
        return totals

    # ------------------------------------------------------------------
    # the parity assertions
    # ------------------------------------------------------------------
    def test_scenarios_match_the_shared_expectations(self):
        for scenario in SCENARIOS:
            missing = [
                m for m in scenario["requires"] if not self._module_installed(m)
            ]
            self.assertFalse(
                missing,
                "Scenario %s needs %s. Install it in BOTH payroll databases, "
                "or the comparison covers less than it appears to."
                % (scenario["key"], missing),
            )
            with self.subTest(scenario=scenario["key"]):
                totals = self._totals(self._build_slip(scenario))
                for concept, expected in scenario["expected"].items():
                    actual = sum(
                        totals.get(code, 0.0)
                        for code in codes_for(concept, self.engine, COUNTRY_CZ)
                    )
                    self.assertAlmostEqual(
                        actual,
                        expected,
                        places=2,
                        msg=(
                            "engine=%s scenario=%s concept=%s: expected %.2f, "
                            "got %.2f. The other engine is held to the same "
                            "number." % (self.engine, scenario["key"],
                                         concept, expected, actual)
                        ),
                    )

    def test_average_earnings_match_across_engines(self):
        """The průměrný výdělek is the rate every náhrada is built from, so a
        divergence in it moves them all at once."""
        for scenario in AVG_EARNINGS_SCENARIOS:
            with self.subTest(scenario=scenario["key"]):
                slip = self._build_slip(scenario)
                self.assertAlmostEqual(
                    slip.l10n_cz_average_hourly_earnings(),
                    scenario["expected_hourly"],
                    places=2,
                    msg="engine=%s scenario=%s" % (self.engine, scenario["key"]),
                )

    def test_every_canonical_code_resolves_on_this_engine(self):
        """A concept whose rule codes do not exist here is a silent zero.

        ``sum(totals.get(code, 0.0) ...)`` cannot tell "the rule produced no
        line" from "the rule does not exist", so a renamed rule would read as
        0.00 and quietly agree with an engine that also produced 0.00.
        """
        existing = set(self.env["hr.salary.rule"].search([]).mapped("code"))
        unknown = {}
        for concept in {c for s in SCENARIOS for c in s["expected"]}:
            for code in codes_for(concept, self.engine, COUNTRY_CZ):
                if code not in existing:
                    unknown.setdefault(concept, []).append(code)
        self.assertFalse(
            unknown,
            "Rule codes named in parity_cz.py do not exist on engine %s: %s. "
            "Either the rule was renamed (update RULE_CODES) or the module "
            "providing it is not installed." % (self.engine, unknown),
        )
