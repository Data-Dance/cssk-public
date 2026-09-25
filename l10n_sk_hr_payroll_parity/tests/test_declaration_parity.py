# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Assert the declaration modules report the same figures on both engines.

Payroll parity (``test_parity.py``) proves the two engines compute the same
payslip. That is not sufficient: every declaration module reads payslip lines
BY RULE CODE, and the codes differ per engine — income tax is one line on one
engine and two on the other, the health top-up is spelled two ways. A module
that resolved only one engine's spelling would emit a plausible 0.00 and its
own test, which compares against the payslip sitting next to it in the same
database, would pass.

The expected figures here are therefore fixed constants derived by hand from
the statutory rates, never read back from the payslip.
"""

import base64

from lxml import etree

from odoo.addons.l10n_sk_hr_payroll_parity.parity import (
    ANNUAL_DECLARATION_MONTHS,
    ANNUAL_DECLARATION_SCENARIOS,
    DECLARATION_DOHODA_WAGE,
    DECLARATION_PERIOD,
    DECLARATION_SCENARIOS,
    DECLARATION_WAGE,
    ENGINE_OCA,
)
from odoo.tests import TransactionCase, tagged


def findtext_local(root, path):
    """Find text by slash-separated LOCAL element names, ignoring namespaces.

    The family mixes namespaced schemas (MVPP) with un-namespaced ones
    (Prehľad); matching on local names keeps the scenario table readable
    instead of carrying a namespace map per form.

    A trailing ``@name`` reads an ATTRIBUTE instead of the element text. The
    VPP annex carries its per-employee figures as attributes, so without this
    the only assertable parts of that form would be its totals.
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
class TestDeclarationParity(TransactionCase):
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
        # Every identifier any form in the family asks for, so one company
        # serves all of them.
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK Declaration Parity Co",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "12345678",
                # The ELDP refuses to render without a korAdresa.
                "street": "Hlavna 1",
                "city": "Bratislava",
                "zip": "81101",
            }
        )
        for field, value in (
            ("l10n_sk_dic", "1234567890"),
            ("l10n_sk_sp_vs", "1234567890"),
            ("l10n_sk_health_payer_number", "1234567890"),
            ("l10n_sk_health_insurer_code", "24"),
        ):
            if field in cls.company._fields:
                cls.company[field] = value
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": cls.company.id}
        )
        cls.company.resource_calendar_id = cls.calendar
        cls._make_payslip()

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        ):
            return ENGINE_OCA
        return "ee"

    @classmethod
    def _make_payslip(cls):
        (y1, m1, d1), (y2, m2, d2) = DECLARATION_PERIOD
        from datetime import date

        emp_vals = {
            "name": "Jozko Mrkvicka",
            "company_id": cls.company.id,
            "resource_calendar_id": cls.calendar.id,
            "identification_id": "8501011234",
            # The ELDP needs a date of birth for <datNarodenia>; it matches the
            # rodné číslo above so the two are not quietly inconsistent.
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
        employee.version_id.write(
            {
                "l10n_sk_tax_declaration_signed": True,
                "resource_calendar_id": cls.calendar.id,
            }
        )
        slip_vals = {
            "name": "Declaration parity",
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
        cls.employee, cls.slip = employee, slip

    def _module_installed(self, name):
        return bool(
            self.env["ir.module.module"].search_count(
                [("name", "=", name), ("state", "=", "installed")]
            )
        )

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
                vals = dict(scenario["create"], company_id=self.company.id)
                decl = (
                    self.env[scenario["model"]]
                    .with_company(self.company)
                    .create(vals)
                )
                decl.action_generate()
                root = etree.fromstring(
                    base64.b64decode(decl.xml_attachment_id.datas)
                )
                for path, expected in scenario["expected"].items():
                    text = findtext_local(root, path)
                    self.assertIsNotNone(
                        text,
                        "engine=%s %s: no element at %r in the generated XML"
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
        # under test in this database — skip, visibly. A PARTIAL install is a
        # different thing entirely: it looks like coverage and is not, so that
        # still fails.
        if not ran and skipped:
            self.skipTest(
                "No declaration module installed in this database; the "
                "reporting family is not under test here. Missing: %s"
                % sorted({m for _key, mods in skipped for m in mods})
            )
        self.assertTrue(ran, "No declaration scenario ran at all")
        if skipped:
            self.fail(
                "Declaration scenarios skipped for want of modules: %s. Some "
                "ran and some did not, so this run covers less than it "
                "appears to. Install them in BOTH payroll databases." % skipped
            )

    # ------------------------------------------------------------------
    # VPP / MVP population split — its own fixture, deliberately
    # ------------------------------------------------------------------
    def _dohoda_structure(self):
        """The DoPČ structure (OCA) or structure type (Enterprise).

        The structure decides the employment form and a contract may not
        disagree with it, so a dohoda fixture has to sit on the matching one
        rather than setting the agreement type underneath a structure that
        says "employment".
        """
        xmlid = (
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_dopc"
            if self.engine == ENGINE_OCA
            else "l10n_sk_hr_payroll_ee.structure_type_dopc_sk"
        )
        return self.env.ref(xmlid, raise_if_not_found=False)

    def _make_dohodar(self, struct):
        from datetime import date

        (y1, m1, d1), (y2, m2, d2) = DECLARATION_PERIOD
        emp_vals = {
            "name": "Dohodar Dusan",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": "9002022345",
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": DECLARATION_DOHODA_WAGE,
        }
        if self.engine == ENGINE_OCA:
            emp_vals["struct_id"] = struct.id
        else:
            emp_vals["structure_type_id"] = struct.id
        employee = (
            self.env["hr.employee"].with_company(self.company).create(emp_vals)
        )
        version_vals = {"resource_calendar_id": self.calendar.id}
        if "l10n_sk_income_regular" in employee.version_id._fields:
            version_vals["l10n_sk_income_regular"] = False
        if self.engine == ENGINE_OCA:
            version_vals["struct_id"] = struct.id
        employee.version_id.write(version_vals)

        payslip_struct = (
            struct if self.engine == ENGINE_OCA else struct.default_struct_id
        )
        slip_vals = {
            "name": "Dohoda parity slip",
            "employee_id": employee.id,
            "struct_id": payslip_struct.id,
            "company_id": self.company.id,
            "date_from": date(y1, m1, d1),
            "date_to": date(y2, m2, d2),
        }
        if self.engine == ENGINE_OCA:
            slip_vals["contract_id"] = employee.version_id.id
        else:
            slip_vals["version_id"] = employee.version_id.id
        slip = self.env["hr.payslip"].with_company(self.company).create(slip_vals)
        if self.engine != ENGINE_OCA:
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        return employee

    def _generate_xml(self, model, create_vals):
        decl = self.env[model].with_company(self.company).create(
            dict(create_vals, company_id=self.company.id)
        )
        decl.action_generate()
        return etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))

    def test_irregular_income_goes_to_the_vpp_not_the_mvp(self):
        """The Sociálna poisťovňa splits its two monthly forms by income
        regularity: regular belongs on the MVP, irregular (dohody) on the VPP.

        This gets its OWN fixture rather than joining DECLARATION_SCENARIOS.
        Those aggregate over the whole company, so a second employee moves
        every figure in them — adding this dohodár to the shared fixture took
        the MVP total from 692.00 to 811.20 and the Prehľad base from 2000 to
        2400. TransactionCase rolls this back, so the hand-derived constants
        next door are untouched.
        """
        if not self._module_installed("l10n_sk_hr_payroll_vpp"):
            self.skipTest("l10n_sk_hr_payroll_vpp is not installed")
        struct = self._dohoda_structure()
        self.assertTrue(struct, "the DoPČ structure must exist")
        self._make_dohodar(struct)

        vpp = self._generate_xml("l10n.sk.vpp", {"year": "2026", "month": "3"})
        base = findtext_local(
            vpp, "priloha/poistneZamestnancov/poistneZamestnanca@vzSp"
        )
        self.assertIsNotNone(base, "the dohodár must appear on the VPP")
        # Only the 400 EUR dohoda may be here. If the scoping ever broke, the
        # 2000 EUR employee from the shared fixture would show up too.
        self.assertAlmostEqual(float(base), DECLARATION_DOHODA_WAGE, places=2)
        self.assertEqual(
            len(
                [
                    node
                    for node in vpp.iter()
                    if etree.QName(node).localname == "poistneZamestnanca"
                ]
            ),
            1,
            "the regular-income employee must not be on the VPP",
        )

    # ------------------------------------------------------------------
    # Annual forms — twelve payslips, in their own fixture
    # ------------------------------------------------------------------
    def _complete_the_year(self):
        """Give the fixture employee the other eleven months of 2026.

        Reusing the setUpClass employee rather than adding a second one: an
        annual figure sums everything in the company for the year, so a second
        population would have to be added to every expectation — the first
        attempt did exactly that and produced 26000 against a hand-derived
        24000. One employee, twelve payslips, twelve times a monthly constant.

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

    def test_annual_declarations_report_the_shared_figures(self):
        """The ELDP and the Hlásenie, against twelve times a monthly constant.

        The monthly scenarios already pin 2000.00 of base and a 230.81 advance
        by hand, so the annual forms are held to the same numbers rather than
        to whatever their own aggregation happens to produce.
        """
        installed = [
            sc for sc in ANNUAL_DECLARATION_SCENARIOS
            if all(self._module_installed(m) for m in sc["requires"])
        ]
        if not installed:
            self.skipTest(
                "No annual declaration module installed in this database")
        self.assertEqual(
            len(installed), len(ANNUAL_DECLARATION_SCENARIOS),
            "a PARTIAL install looks like coverage and is not: %s"
            % [sc["key"] for sc in ANNUAL_DECLARATION_SCENARIOS
               if sc not in installed],
        )

        # One employee, one full year.
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
                        float(text), expected, places=2,
                        msg=(
                            "engine=%s scenario=%s path=%s: the declaration "
                            "reports %s where the statutory figure is %.2f."
                            % (self.engine, scenario["key"], path, text,
                               expected)
                        ),
                    )

    def test_eldp_still_reports_no_excluded_days(self):
        """Pins a KNOWN GAP so it cannot be closed silently.

        ``dni_vyluc`` is a hardcoded 0 in l10n_sk_eldp, and QWeb drops a falsy
        ``t-att`` entirely, so ``dniVyluc`` never reaches the XML. Vylúčené
        doby are real — materská, rodičovská and PN days all produce them — so
        this is wrong for any employee who had one. The day it starts being
        derived, this test fails and says why, rather than the change passing
        unnoticed.
        """
        if not self._module_installed("l10n_sk_hr_payroll_eldp"):
            self.skipTest("l10n_sk_hr_payroll_eldp is not installed")
        self._complete_the_year()
        root = self._generate_xml("l10n.sk.eldp", {"year": "2026"})
        self.assertIsNone(
            findtext_local(root, "obdobiaPoist/vzZaObdobiePoist@dniVyluc"),
            "dniVyluc is now in the XML. If vylúčené doby are being derived, "
            "good — update this test and the ELDP scenario to assert the "
            "figure instead of its absence.",
        )
