# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Assert the Czech declaration modules report the same figures on both engines.

Payroll parity (``test_parity.py``) proves the two engines compute the same
payslip. That is not sufficient: every declaration module reads payslip lines
BY RULE CODE, and a module that resolved only one engine's spelling would emit
a plausible 0.00 — and its own test, which compares against the payslip sitting
next to it in the same database, would pass.

The expected figures here are fixed constants derived by hand from the
statutory rates, never read back from the payslip. That is the whole point: a
test that reads the implementation back agrees with whatever the implementation
does, including the wrong thing.
"""

import base64

from lxml import etree

from odoo.addons.l10n_cz_hr_payroll_parity.parity_cz import (
    ANNUAL_DECLARATION_MONTHS,
    ANNUAL_DECLARATION_SCENARIOS,
    DECLARATION_PERIOD,
    DECLARATION_SCENARIOS,
    DECLARATION_WAGE,
    ENGINE_OCA,
)
from odoo.tests import TransactionCase, tagged

OCA_STRUCT = "l10n_cz_hr_payroll_oca.hr_payroll_structure_cz_employee_salary"
EE_STRUCT = "l10n_cz_hr_payroll_ee.hr_payroll_structure_cz_employee_salary"


def findtext_local(root, path):
    """Find text by slash-separated LOCAL element names, ignoring namespaces.

    A trailing ``@name`` reads an attribute instead of the element text.
    Matching on local names keeps the scenario table readable instead of
    carrying a namespace map per form.
    """
    attr = None
    if "@" in path:
        path, attr = path.split("@", 1)
        path = path.rstrip("/")
    nodes = [root]
    for name in path.split("/"):
        nxt = []
        for node in nodes:
            nxt.extend(
                child
                for child in node.iter()
                if etree.QName(child).localname == name and child is not node
            )
        if not nxt:
            return None
        nodes = nxt
    if attr is not None:
        return nodes[0].get(attr)
    return nodes[0].text


@tagged("post_install", "-at_install")
class TestCzDeclarationParity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        if cls.engine == ENGINE_OCA:
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = cls.env.ref(OCA_STRUCT)
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager"
            )
            cls.structure = cls.env.ref(EE_STRUCT)
        # Every identifier any form in the family asks for, so one company
        # serves all of them.
        cls.company = cls.env["res.company"].create(
            {
                "name": "CZ Declaration Parity Co",
                "country_id": cls.env.ref("base.cz").id,
                "currency_id": cls.env.ref("base.CZK").id,
                "company_registry": "12345678",
                # The Vyúčtování needs a DIČ for <VetaP dic>.
                # Checksum-valid: base_vat validates DIČ where it is
                # installed, and CZ12345678 fails that check.
                "vat": "CZ12345679",
                "street": "Hlavni 1",
                "city": "Praha",
                "zip": "11000",
            }
        )
        for field, value in (
            ("l10n_cz_ossz_code", "101"),
            ("l10n_cz_ossz_vs", "1234567890"),
            ("l10n_cz_health_insurer_code", "111"),
            # The Vyúčtování needs the receiving tax office.
            ("l10n_cz_fu_code", "451"),
        ):
            if field in cls.company._fields:
                cls.company[field] = value
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "CZ 40h/week", "company_id": cls.company.id}
        )
        cls.company.resource_calendar_id = cls.calendar
        cls._make_payslip()

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(OCA_STRUCT, raise_if_not_found=False):
            return ENGINE_OCA
        return "ee"

    @classmethod
    def _make_payslip(cls):
        from datetime import date

        (y1, m1, d1), (y2, m2, d2) = DECLARATION_PERIOD
        emp_vals = {
            "name": "Jan Novak",
            "company_id": cls.company.id,
            "resource_calendar_id": cls.calendar.id,
            "identification_id": "8501011234",
            "birthday": date(1985, 1, 1),
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": DECLARATION_WAGE,
        }
        if cls.engine == ENGINE_OCA:
            emp_vals["struct_id"] = cls.structure.id
        else:
            emp_vals["structure_type_id"] = cls.structure.type_id.id
        employee = (
            cls.env["hr.employee"].with_company(cls.company).create(emp_vals)
        )
        version_vals = {
            "resource_calendar_id": cls.calendar.id,
            "l10n_cz_tax_declaration": True,
        }
        if cls.engine == ENGINE_OCA:
            version_vals["struct_id"] = cls.structure.id
        employee.version_id.write(version_vals)

        slip_vals = {
            "name": "CZ declaration parity slip",
            "employee_id": employee.id,
            "struct_id": cls.structure.id,
            "company_id": cls.company.id,
            "date_from": date(y1, m1, d1),
            "date_to": date(y2, m2, d2),
        }
        if cls.engine == ENGINE_OCA:
            slip_vals["contract_id"] = employee.version_id.id
        else:
            slip_vals["version_id"] = employee.version_id.id
        slip = cls.env["hr.payslip"].with_company(cls.company).create(slip_vals)
        if cls.engine != ENGINE_OCA:
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        slip.write(
            {"state": "done" if cls.engine == ENGINE_OCA else "validated"}
        )
        cls.employee, cls.slip = employee, slip

    def _module_installed(self, name):
        return bool(
            self.env["ir.module.module"].search_count(
                [("name", "=", name), ("state", "=", "installed")]
            )
        )

    def _generate_xml(self, model, create_vals):
        decl = (
            self.env[model]
            .with_company(self.company)
            .create(dict(create_vals, company_id=self.company.id))
        )
        decl.action_generate()
        return etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))

    def test_declarations_report_the_shared_figures(self):
        ran, skipped = [], []
        for scenario in DECLARATION_SCENARIOS:
            missing = [
                m for m in scenario["requires"] if not self._module_installed(m)
            ]
            if missing:
                skipped.append((scenario["key"], missing))
                continue
            with self.subTest(scenario=scenario["key"]):
                root = self._generate_xml(scenario["model"], scenario["create"])
                for path, expected in scenario["expected"].items():
                    text = findtext_local(root, path)
                    self.assertIsNotNone(
                        text,
                        "engine=%s scenario=%s: %s is missing from the XML"
                        % (self.engine, scenario["key"], path),
                    )
                    self.assertAlmostEqual(
                        float(text),
                        expected,
                        places=2,
                        msg=(
                            "engine=%s scenario=%s path=%s: the declaration "
                            "reports %s where the statutory figure is %.2f. "
                            "Check the rule codes the module reads before "
                            "touching the expectation."
                            % (self.engine, scenario["key"], path, text, expected)
                        ),
                    )
            # Outside the subTest on purpose: a scenario that RAN and
            # failed has still been covered. Counting it as "did not
            # run" adds a second, misleading failure on top of the
            # real one.
            ran.append(scenario["key"])

        # Nothing installed at all means the reporting family simply is not
        # under test here — skip, visibly. A PARTIAL install is a different
        # thing: it looks like coverage and is not, so that still fails.
        if not ran and skipped:
            self.skipTest(
                "No Czech declaration module installed in this database. "
                "Missing: %s"
                % sorted({m for _key, mods in skipped for m in mods})
            )
        self.assertTrue(ran, "No declaration scenario ran at all")
        if skipped:
            self.fail(
                "Declaration scenarios skipped for want of modules: %s. Some "
                "ran and some did not, so this run covers less than it appears "
                "to. Install them in BOTH payroll databases." % skipped
            )

    # ------------------------------------------------------------------
    # Annual forms — twelve payslips, in their own fixture
    # ------------------------------------------------------------------
    def _complete_the_year(self):
        """Give the fixture employee the other eleven months of 2026.

        Reusing the setUpClass employee rather than adding a second one: an
        annual figure sums everything in the company for the year, so a second
        population would have to be added to every expectation. One employee,
        twelve payslips, twelve times a monthly constant.

        Built here rather than in setUpClass because the monthly scenarios must
        keep seeing exactly one payslip; TransactionCase rolls this back.
        """
        import calendar as _cal
        from datetime import date

        (_y1, march, _d1), _to = DECLARATION_PERIOD
        for month in range(1, ANNUAL_DECLARATION_MONTHS + 1):
            if month == march:
                continue  # already seeded by setUpClass
            last = _cal.monthrange(2026, month)[1]
            slip_vals = {
                "name": "Annual slip %02d" % month,
                "employee_id": self.employee.id,
                "struct_id": self.structure.id,
                "company_id": self.company.id,
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, last),
            }
            if self.engine == ENGINE_OCA:
                slip_vals["contract_id"] = self.employee.version_id.id
            else:
                slip_vals["version_id"] = self.employee.version_id.id
            slip = (
                self.env["hr.payslip"].with_company(self.company).create(slip_vals)
            )
            if self.engine != ENGINE_OCA:
                slip = slip.with_context(salary_simulation=True)
            slip.compute_sheet()
            slip.write(
                {"state": "done" if self.engine == ENGINE_OCA else "validated"}
            )

    def test_annual_declarations_report_the_shared_figures(self):
        """The ELDP and the Vyúčtování, against twelve times a monthly constant.

        The CZ payroll suite already pins 50 000.00 of gross and a 4 930 CZK
        advance (15 % less the sleva) by hand, so the annual forms are held to
        those rather than to whatever their own aggregation produces.
        """
        installed = [
            sc
            for sc in ANNUAL_DECLARATION_SCENARIOS
            if all(self._module_installed(m) for m in sc["requires"])
        ]
        if not installed:
            self.skipTest(
                "No annual Czech declaration module installed in this database"
            )
        self.assertEqual(
            len(installed),
            len(ANNUAL_DECLARATION_SCENARIOS),
            "a PARTIAL install looks like coverage and is not: %s"
            % [
                sc["key"]
                for sc in ANNUAL_DECLARATION_SCENARIOS
                if sc not in installed
            ],
        )
        self._complete_the_year()

        for scenario in installed:
            with self.subTest(scenario=scenario["key"]):
                root = self._generate_xml(scenario["model"], scenario["create"])
                for path, expected in scenario["expected"].items():
                    text = findtext_local(root, path)
                    self.assertIsNotNone(
                        text,
                        "engine=%s scenario=%s: %s is missing from the XML"
                        % (self.engine, scenario["key"], path),
                    )
                    self.assertAlmostEqual(
                        float(text),
                        expected,
                        places=2,
                        msg=(
                            "engine=%s scenario=%s path=%s: the declaration "
                            "reports %s where the statutory figure is %.2f."
                            % (self.engine, scenario["key"], path, text, expected)
                        ),
                    )

    def test_annual_declarations_report_the_shared_figures(self):
        """The ELDP and the Vyúčtování, against twelve times a monthly constant.

        The CZ payroll suite already pins 50 000.00 of gross and a 4 930 CZK
        advance (15 % less the sleva) by hand, so the annual forms are held to
        those rather than to whatever their own aggregation produces.
        """
        installed = [
            sc
            for sc in ANNUAL_DECLARATION_SCENARIOS
            if all(self._module_installed(m) for m in sc["requires"])
        ]
        if not installed:
            self.skipTest(
                "No annual Czech declaration module installed in this database"
            )
        self.assertEqual(
            len(installed),
            len(ANNUAL_DECLARATION_SCENARIOS),
            "a PARTIAL install looks like coverage and is not: %s"
            % [
                sc["key"]
                for sc in ANNUAL_DECLARATION_SCENARIOS
                if sc not in installed
            ],
        )
        self._complete_the_year()

        for scenario in installed:
            with self.subTest(scenario=scenario["key"]):
                root = self._generate_xml(scenario["model"], scenario["create"])
                for path, expected in scenario["expected"].items():
                    text = findtext_local(root, path)
                    self.assertIsNotNone(
                        text,
                        "engine=%s scenario=%s: %s is missing from the XML"
                        % (self.engine, scenario["key"], path),
                    )
                    self.assertAlmostEqual(
                        float(text),
                        expected,
                        places=2,
                        msg=(
                            "engine=%s scenario=%s path=%s: the declaration "
                            "reports %s where the statutory figure is %.2f."
                            % (self.engine, scenario["key"], path, text, expected)
                        ),
                    )

    def _assert_internally_consistent(self, root, scenario):
        """Assert a form agrees with ITSELF where the figure is unresolved.

        The Vyúčtování reports the same quantity twice — once per month in
        Part I and once as a yearly total in Part II — and whichever of the two
        candidate tax figures turns out to be right, those two must match. That
        is assertable today; the figure is not, so it is not asserted.
        """
        spec = scenario.get("internally_consistent")
        if not spec:
            return
        monthly = findtext_local(root, spec["monthly"])
        annual = findtext_local(root, spec["annual"])
        self.assertIsNotNone(monthly, "%s is missing" % spec["monthly"])
        self.assertIsNotNone(annual, "%s is missing" % spec["annual"])
        self.assertAlmostEqual(
            float(monthly) * spec["months"],
            float(annual),
            places=2,
            msg=(
                "engine=%s scenario=%s: %s months of %s = %s does not match "
                "the annual %s = %s. One part is reading a different rule code "
                "from the other."
                % (self.engine, scenario["key"], spec["months"],
                   spec["monthly"], monthly, spec["annual"], annual)
            ),
        )
