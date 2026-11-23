# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The fund bases a payslip records are the same on both payroll engines.

The insurance declarations read the recorded rows through the engine's
reader. This suite computes the shared scenarios on whichever engine the
database has and compares the rows, and the health statement generated from
them, with one set of expectations.
"""

import base64
from datetime import date
from decimal import Decimal

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
from odoo.addons.l10n_sk_hr_payroll_parity.parity import (
    ENGINE_OCA,
    RECORDED_FUND_PERIOD,
    RECORDED_FUND_SCENARIOS,
)
from odoo.tests import TransactionCase, tagged

from .test_declaration_parity import findtext_local


@tagged("post_install", "-at_install")
class TestRecordedFundParity(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        oca = cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        )
        cls.engine = ENGINE_OCA if oca else "ee"
        if oca:
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = oca
        else:
            cls.env.user.group_ids |= cls.env.ref(
                "hr_payroll.group_hr_payroll_manager"
            )
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary"
            )
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK Recorded Fund Parity Co",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "12345679",
            }
        )
        for field, value in (
            ("l10n_sk_dic", "1234567890"),
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

    def _short_week(self):
        return self.env["resource.calendar"].create(
            {
                "name": "SK 5h/week",
                "company_id": self.company.id,
                "full_time_required_hours": 40.0,
                "hours_per_day": 1.0,
                "attendance_ids": [(5, 0, 0)]
                + [
                    (0, 0, {
                        "name": "Day %d" % day,
                        "dayofweek": str(day),
                        "hour_from": 8.0,
                        "hour_to": 9.0,
                        "day_period": "morning",
                    })
                    for day in range(5)
                ],
            }
        )

    def _payslip(self, scenario):
        """A really computed, confirmed payslip: a simulation records nothing."""
        calendar = self._short_week() if scenario["short_week"] else self.calendar
        first, last = (date(*day) for day in RECORDED_FUND_PERIOD)
        values = {
            "name": "Zamestnanec %s" % scenario["key"],
            "company_id": self.company.id,
            "resource_calendar_id": calendar.id,
            "identification_id": "8501011234",
        }
        version = dict(scenario["version"])
        if self.engine == ENGINE_OCA:
            version.update(
                contract_date_start=date(2026, 1, 1),
                date_version=date(2026, 1, 1),
                wage=scenario["wage"],
                resource_calendar_id=calendar.id,
                struct_id=self.structure.id,
            )
        else:
            values.update(
                date_version=date(2026, 1, 1),
                contract_date_start=date(2026, 1, 1),
                wage=scenario["wage"],
                structure_type_id=self.structure.type_id.id,
            )
        employee = self.env["hr.employee"].with_company(self.company).create(values)
        if version:
            employee.version_id.write(version)
        slip_values = {
            "name": "Recorded fund parity %s" % scenario["key"],
            "employee_id": employee.id,
            "struct_id": self.structure.id,
            "company_id": self.company.id,
            "date_from": first,
            "date_to": last,
        }
        Payslip = self.env["hr.payslip"].with_company(self.company)
        if self.engine == ENGINE_OCA:
            slip_values["contract_id"] = employee.version_id.id
            slip = Payslip.create(slip_values)
            slip.worked_days_line_ids = [
                (0, 0, line)
                for line in slip.get_worked_day_lines(
                    employee.version_id, first, last
                )
            ]
        else:
            slip_values["version_id"] = employee.version_id.id
            slip = Payslip.create(slip_values)
        slip.compute_sheet()
        confirm_payslips(slip)
        return slip

    def test_both_engines_read_the_same_recorded_rows(self):
        for scenario in RECORDED_FUND_SCENARIOS:
            slip = self._payslip(scenario)
            self.assertTrue(
                callable(getattr(slip, "_cssk_recorded_fund_bases", None)),
                "engine=%s has no reader of the recorded fund bases" % self.engine,
            )
            rows = {
                (row["fund"], row["side"]): row
                for row in slip._cssk_recorded_fund_bases() or []
            }
            self.assertEqual(
                set(rows), set(scenario["rows"]),
                "engine=%s scenario=%s" % (self.engine, scenario["key"]),
            )
            for key, expected in scenario["rows"].items():
                with self.subTest(scenario=scenario["key"], fund=key):
                    row = rows[key]
                    self.assertEqual(
                        tuple(Decimal(row[name]) for name in ("base", "rate", "amount")),
                        tuple(Decimal(str(value)) for value in expected),
                        "engine=%s scenario=%s %s/%s: the payslip recorded "
                        "another base, rate or amount than both engines "
                        "must." % ((self.engine, scenario["key"]) + key),
                    )

    def test_health_statement_reads_the_recorded_base(self):
        if "l10n.sk.health" not in self.env:
            self.skipTest("l10n_sk_hr_payroll_health is not installed")
        for scenario in RECORDED_FUND_SCENARIOS:
            if "statement" not in scenario:
                continue
            with self.subTest(scenario=scenario["key"]):
                slip = self._payslip(scenario)
                declaration = (
                    self.env["l10n.sk.health"]
                    .with_company(self.company)
                    .create({"company_id": self.company.id, "year": "2026",
                             "month": "3"})
                )
                declaration.action_generate()
                self.assertFalse(
                    declaration.fund_bases_warning,
                    "engine=%s: the statement fell back to gross for %s"
                    % (self.engine, slip.display_name),
                )
                root = etree.fromstring(
                    base64.b64decode(declaration.xml_attachment_id.datas)
                )
                for path, expected in scenario["statement"].items():
                    text = findtext_local(root, path)
                    self.assertIsNotNone(text, path)
                    self.assertAlmostEqual(
                        float(text), expected, places=2,
                        msg="engine=%s scenario=%s path=%s reports %s, not %.2f"
                        % (self.engine, scenario["key"], path, text, expected),
                    )
