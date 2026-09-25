# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drive the shared scenarios through whichever payroll engine is installed.

The two engines cannot coexist in one database — both claim ``hr.payslip`` —
so parity cannot be asserted inside a single run. Instead this one test file is
installed in BOTH engines' databases and asserts against the SAME expected
figures in ``parity.py``. Divergence therefore fails on whichever side moved.

That makes the CI contract explicit: this module must be installed in both
payroll databases, and both runs must be green. One green run proves half of
the property and is not evidence of parity.
"""

from datetime import date

from odoo.addons.l10n_sk_hr_payroll_parity.parity import (
    AVG_EARNINGS_SCENARIOS,
    ENGINE_EE,
    ENGINE_OCA,
    LEAVE_SCENARIOS,
    SCENARIOS,
    codes_for,
)
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPayrollEngineParity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        if cls.engine == ENGINE_OCA:
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
            )
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager"
            )
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary"
            )
        cls.company = cls.env["res.company"].create(
            {"name": "SK Parity Co", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        # An explicit calendar on both sides: the minimum-wage proration divides
        # by the company calendar's hours, so leaving it implicit would compare
        # two different denominators and call the difference an engine bug.
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.company.resource_calendar_id = cls.calendar

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        ):
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
    def _build(self, scenario):
        """Materialise *scenario* on this engine and return {code: total}."""
        slip = self._build_slip(scenario)
        totals = {}
        for line in slip.line_ids:
            totals[line.code] = totals.get(line.code, 0.0) + line.total
        return totals

    def _build_slip(self, scenario):
        """Materialise *scenario* and return the computed payslip."""
        (y1, m1, d1), (y2, m2, d2) = scenario["period"]
        date_from, date_to = date(y1, m1, d1), date(y2, m2, d2)

        calendar = self._scenario_calendar(scenario)
        emp_vals = {
            "name": "Parity %s" % scenario["key"],
            "company_id": self.company.id,
            "resource_calendar_id": calendar.id,
            "date_version": date(2024, 1, 1),
            "contract_date_start": date(2024, 1, 1),
            "wage": scenario["wage"],
        }
        if self.engine == ENGINE_OCA:
            emp_vals["struct_id"] = self.structure.id
        else:
            emp_vals["structure_type_id"] = self.structure.type_id.id
        employee = (
            self.env["hr.employee"].with_company(self.company).create(emp_vals)
        )
        version_vals = dict(scenario["version"])
        version_vals["resource_calendar_id"] = calendar.id
        if self.engine == ENGINE_OCA:
            version_vals["struct_id"] = self.structure.id
        employee.version_id.write(version_vals)

        slip_vals = {
            "name": "Parity %s" % scenario["key"],
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": date_from,
            "date_to": date_to,
        }
        if self.engine == ENGINE_OCA:
            slip_vals["contract_id"] = employee.version_id.id
            slip_vals["input_line_ids"] = [
                (
                    0,
                    0,
                    {
                        "name": code,
                        "code": code,
                        "amount": qty,
                        "contract_id": employee.version_id.id,
                    },
                )
                for code, qty in scenario["inputs"].items()
            ]
        else:
            slip_vals["version_id"] = employee.version_id.id
            slip_vals["input_line_ids"] = [
                (0, 0, {"input_type_id": self._input_type(code).id, "amount": qty})
                for code, qty in scenario["inputs"].items()
            ]
        for name, d_from, d_to in scenario.get("leaves", ()):
            self._book_leave(employee, name, date(*d_from), date(*d_to))
        slip = self.env["hr.payslip"].with_company(self.company).create(slip_vals)
        if self.engine == ENGINE_OCA and scenario.get("leaves"):
            # The OCA engine fills worked-day lines from an onchange, which does
            # not fire on create() in a test. Without them there is no WORK100
            # and no leave line, so an absence scenario would silently compare
            # two untouched full-month payslips and pass.
            worked = slip.get_worked_day_lines(
                employee.version_id, date_from, date_to
            )
            slip.worked_days_line_ids = [(0, 0, line) for line in worked]
        if self.engine == ENGINE_EE and not scenario.get("leaves"):
            # Enterprise only materialises worked-day lines on a real run, so a
            # leave-driven scenario must not be simulated.
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        return slip

    def _scenario_calendar(self, scenario):
        """The shared 40 h/week calendar, unless the scenario asks for its own.

        ``calendar_hours`` maps dayofweek -> hours, so a scenario can pin a
        week that is 40 hours WITHOUT being 8 hours every day. That shape is
        ordinary in Slovak practice (kratší piatok) and it is the one where
        proration by days and payment by hours stop agreeing.
        """
        hours = scenario.get("calendar_hours")
        if not hours:
            return self.calendar
        return self.env["resource.calendar"].create(
            {
                "name": "Parity %s" % scenario["key"],
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

    def _book_leave(self, employee, record_name, d_from, d_to):
        """Resolve a leave type by RECORD NAME against whichever localisation
        is installed, so one scenario drives both engines."""
        module = (
            "l10n_sk_hr_payroll_oca"
            if self.engine == ENGINE_OCA
            else "l10n_sk_hr_payroll_ee"
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
        leave.action_approve()
        return leave

    def _input_type(self, code):
        itype = self.env["hr.payslip.input.type"].search([("code", "=", code)], limit=1)
        self.assertTrue(itype, "No hr.payslip.input.type with code %r" % code)
        return itype

    # ------------------------------------------------------------------
    # the parity assertions
    # ------------------------------------------------------------------
    def test_scenarios_match_the_shared_expectations(self):
        ran, skipped = [], []
        for scenario in SCENARIOS:
            missing = [
                m for m in scenario["requires"] if not self._module_installed(m)
            ]
            if missing:
                skipped.append((scenario["key"], missing))
                continue
            with self.subTest(scenario=scenario["key"]):
                totals = self._build(scenario)
                for concept, expected in scenario.get("expected_abs", {}).items():
                    # Magnitude only: some lines legitimately carry opposite
                    # signs on the two engines because each assembles NET its
                    # own way. Asserting the signed value would fail for a
                    # reason that is not a bug; asserting nothing would let the
                    # amount drift. See NOT_COMPARABLE.
                    actual = sum(
                        abs(totals.get(code, 0.0))
                        for code in codes_for(concept, self.engine)
                    )
                    self.assertAlmostEqual(
                        actual, expected, places=2,
                        msg=("engine=%s scenario=%s concept=%s: magnitude "
                             "%.2f, expected %.2f"
                             % (self.engine, scenario["key"], concept,
                                actual, expected)),
                    )
                for concept, expected in scenario["expected"].items():
                    actual = sum(
                        totals.get(code, 0.0)
                        for code in codes_for(concept, self.engine)
                    )
                    self.assertAlmostEqual(
                        actual,
                        expected,
                        places=2,
                        msg=(
                            "engine=%s scenario=%s concept=%s: the other engine "
                            "is expected to produce %.2f but this one produced "
                            "%.2f. Either a rule diverged or the shared "
                            "expectation in parity.py is wrong — do not "
                            "'fix' it by editing the expectation until you "
                            "know which engine is right."
                            % (self.engine, scenario["key"], concept,
                               expected, actual)
                        ),
                    )
                ran.append(scenario["key"])

        self.assertTrue(ran, "No parity scenario ran at all")
        # A silently skipped scenario is indistinguishable from a passing one,
        # which is exactly the failure mode this module exists to remove.
        if skipped:
            self.fail(
                "Parity scenarios skipped for want of modules: %s. Install "
                "them in BOTH payroll databases, or the comparison covers "
                "less than it appears to." % skipped
            )

    def test_every_canonical_code_resolves_on_this_engine(self):
        """A concept whose rule codes do not exist here is a silent zero.

        ``sum(totals.get(code, 0.0) ...)`` cannot tell "the rule produced no
        line" from "the rule does not exist", so a renamed rule would read as
        0.00 and quietly agree with an engine that also produced 0.00.
        """
        rule_model = "hr.salary.rule"
        existing = set(
            self.env[rule_model].search([]).mapped("code")
        )
        unknown = {}
        for concept in {c for s in SCENARIOS for c in s["expected"]}:
            for code in codes_for(concept, self.engine):
                if code not in existing:
                    unknown.setdefault(concept, []).append(code)
        self.assertFalse(
            unknown,
            "Rule codes named in parity.py do not exist on engine %s: %s. "
            "Either the rule was renamed (update CANONICAL_CODES) or the "
            "module providing it is not installed."
            % (self.engine, unknown),
        )

    def test_average_earnings_fallback_matches_across_engines(self):
        """§ 134 ods. 3 pravdepodobný zárobok, asserted on both engines.

        The divisor, not a payslip line: this is the number every náhrada is
        built from, and the two engines used to disagree on it — Enterprise
        divided the wage by a flat 174 monthly hours while OCA used the
        period's own schedule. Nothing in SCENARIOS reached the fallback, so
        the harness was green throughout.
        """
        for scenario in AVG_EARNINGS_SCENARIOS:
            missing = [
                m for m in scenario["requires"] if not self._module_installed(m)
            ]
            self.assertFalse(missing, "missing modules: %s" % missing)
            with self.subTest(scenario=scenario["key"]):
                slip = self._build_slip(scenario)
                self.assertAlmostEqual(
                    slip.l10n_sk_average_hourly_earnings(),
                    scenario["expected_hourly"],
                    places=4,
                    msg=(
                        "engine=%s scenario=%s: average hourly earnings must "
                        "be the wage over THIS period's scheduled hours. A "
                        "difference here moves every dovolenka and paid-"
                        "obstacle náhrada." % (self.engine, scenario["key"])
                    ),
                )

    def test_leave_scenarios_match_the_shared_expectations(self):
        """Absence is the seam where the engines differ most — worked-day codes
        on OCA, work-entry types on Enterprise — and until now no scenario
        booked a leave at all, so none of it was compared."""
        for scenario in LEAVE_SCENARIOS:
            missing = [
                m for m in scenario["requires"] if not self._module_installed(m)
            ]
            self.assertFalse(missing, "missing modules: %s" % missing)
            with self.subTest(scenario=scenario["key"]):
                slip = self._build_slip(scenario)
                totals = {}
                for line in slip.line_ids:
                    totals[line.code] = totals.get(line.code, 0.0) + line.total
                for concept, expected in scenario["expected"].items():
                    actual = sum(
                        totals.get(code, 0.0)
                        for code in codes_for(concept, self.engine)
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
