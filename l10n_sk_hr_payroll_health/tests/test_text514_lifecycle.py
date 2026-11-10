# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from datetime import date

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import confirm_payslips

from .test_health import TestHealth514


@tagged("post_install", "-at_install")
class TestHealthTextLifecycle(TestHealth514):
    def test_two_job_cards_for_one_person_require_consolidation(self):
        self._text_employee(500, weekly_hours=20, rc="8501011234")
        self._text_employee(500, weekly_hours=20, rc="8501011234")
        with self.assertRaises(UserError):
            self._text_report(count=1).action_generate()

    def _text_employee(
        self,
        wage=2000,
        disabled=False,
        op=False,
        rc="8501011234",
        weekly_hours=40,
        full_pn=False,
        minimum_opt_out=False,
        health_periods=None,
    ):
        calendar = self.calendar
        if weekly_hours != 40:
            calendar = self.env["resource.calendar"].create(
                {
                    "name": "Lawful synthetic part-time schedule",
                    "company_id": self.company.id,
                    "hours_per_day": weekly_hours / 5,
                    "attendance_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Work",
                                "dayofweek": str(day),
                                "hour_from": 8,
                                "hour_to": 8 + weekly_hours / 5,
                                "day_period": "morning",
                            },
                        )
                        for day in range(5)
                    ],
                }
            )
        employee = (
            self.env["hr.employee"]
            .with_company(self.company)
            .create(
                {
                    "name": "Synthetic health source",
                    "company_id": self.company.id,
                    "identification_id": rc,
                    "resource_calendar_id": calendar.id,
                    "date_version": date(2026, 1, 1),
                    "contract_date_start": date(2026, 1, 1),
                    "struct_id": self.structure.id,
                    "wage": wage,
                    "l10n_sk_ztp": disabled,
                    "l10n_sk_health_oop_claim": op,
                    "l10n_sk_tax_declaration_signed": False,
                    "l10n_sk_health_insurer_code": "24",
                }
            )
        )
        if health_periods is not None:
            health_calendar = self.env["l10n.sk.health.calendar"].create(
                {
                    "employee_id": employee.id,
                    "company_id": self.company.id,
                    "month": "2026-06-01",
                    "complete": True,
                    "evidence": "Synthetic complete month and notices",
                    "interval_ids": [
                        Command.create(
                            {"kind": kind, "date_start": start, "date_end": end}
                        )
                        for kind, start, end in health_periods
                    ],
                }
            )
            health_calendar.action_review()
        if minimum_opt_out:
            employee.version_id.write(
                {
                    "l10n_sk_health_minimum_opt_out": True,
                    "l10n_sk_health_minimum_evidence": "Synthetic written concurrent-employment notice",
                }
            )
        if full_pn:
            leave_type = self.env["hr.leave.type"].create(
                {
                    "name": "Synthetic PN",
                    "requires_allocation": False,
                    "leave_validation_type": "no_validation",
                    "l10n_sk_payroll_code": "PN",
                }
            )
            leave = self.env["hr.leave"].create(
                {
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date(2026, 6, 1),
                    "request_date_to": date(2026, 6, 30),
                }
            )
            if leave.state != "validate":
                leave.action_validate()
        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "employee_id": employee.id,
                    "company_id": self.company.id,
                    "contract_id": employee.version_id.id,
                    "struct_id": self.structure.id,
                    "date_from": date(2026, 6, 1),
                    "date_to": date(2026, 6, 30),
                }
            )
        )
        # Headless ORM create does not execute the form's onchange. Use the
        # native calendar adapter, as the payroll form/batch wizard does.
        slip.worked_days_line_ids = [Command.clear()] + [
            Command.create(row)
            for row in slip.get_worked_day_lines(
                slip.contract_id, slip.date_from, slip.date_to
            )
        ]
        if full_pn:
            slip.input_line_ids = [
                Command.create(
                    {
                        "name": "Reviewed synthetic daily sickness base",
                        "code": "PN_DVZ",
                        "amount": 100,
                        "contract_id": employee.version_id.id,
                    }
                )
            ]
        slip.compute_sheet()
        confirm_payslips(slip)
        return employee, slip

    def _text_report(self, count=1, **values):
        bank = self.env["res.partner.bank"].search(
            [
                ("partner_id", "=", self.company.partner_id.id),
                ("sanitized_acc_number", "=", "SK3112000000198742637541"),
            ],
            limit=1,
        )
        bank = bank or self.env["res.partner.bank"].create(
            {
                "partner_id": self.company.partner_id.id,
                "acc_number": "SK3112000000198742637541",
            }
        )
        vals = {
            "company_id": self.company.id,
            "year": "2026",
            "month": "6",
            "insurer_code": "24",
            "export_format": "text2023",
            "payment_date": date(2026, 7, 15),
            "sending_date": date(2026, 7, 1),
            "text_payer_number": "9900112233",
            "payment_bank_id": bank.id,
            "registered_count": count,
            "registered_all_insurers_count": count,
        }
        vals.update(values)
        return self.env["l10n.sk.health"].with_company(self.company).create(vals)

    def _records(self, report):
        report.action_generate()
        content = base64.b64decode(report.xml_attachment_id.datas)
        return [row.split("|")[:-1] for row in content.decode().splitlines()]

    def test_native_workflow_exports_both_groups_with_actual_rates_and_money(self):
        self._text_employee()
        self._text_employee(1000, disabled=True, rc="9002022345")
        report = self._text_report(count=2)
        records = self._records(report)
        self.assertEqual(report.xml_attachment_id.name, "N5142606.001")
        self.assertEqual(report.xml_attachment_id.mimetype, "text/plain")
        self.assertEqual(records[2][1:5], ["11,00", "5,00", "5,50", "2,50"])
        self.assertEqual(records[2][5:9], ["1", "1", "30", "30"])
        self.assertEqual(
            records[2][13:18], ["220,00", "100,00", "55,00", "25,00", "400,00"]
        )

    def test_reviewed_state_days_reach_payroll_and_txt_without_using_optout_flag(self):
        self._text_employee(
            100,
            weekly_hours=2,
            health_periods=[
                ("2", "2026-06-01", "2026-06-30"),
                ("state", "2026-06-16", "2026-06-30"),
            ],
        )
        records = self._records(self._text_report())
        self.assertEqual(records[3][2], "30")
        self.assertEqual(records[3][7:10], ["11,00", "5,00", "22,72"])
        self.assertEqual(records[3][15:17], ["0", "6,72"])

    def test_health_calendar_revision_blocks_new_generation_and_keeps_filed_bytes(self):
        employee, slip = self._text_employee(
            health_periods=[("2", "2026-06-01", "2026-06-30")]
        )
        report = self._text_report()
        self._records(report)
        report.action_submit()
        filed = report.submitted_attachment_id
        original = filed.datas
        calendar = employee.l10n_sk_health_calendar_ids
        calendar.action_create_revision()
        self.assertEqual(filed.datas, original)
        self.assertEqual(
            slip._l10n_sk_health_assessment_facts()["calendar_id"], calendar.id
        )
        with self.assertRaises(UserError):
            self._text_report().action_generate()

    def test_op_employee_base_is_not_gross_and_ui_row_uses_the_same_base(self):
        self._text_employee(500, op=True, weekly_hours=20)
        report = self._text_report()
        records = self._records(report)
        self.assertEqual(
            records[3][5:13],
            ["500,00", "360,00", "55,00", "18,00", "73,00", "500,00", "0,00", "140,00"],
        )
        self.assertEqual(report._sheet_lines().vz_base, 360)

    def test_minimum_topup_is_in_employee_header_but_not_employee_row_base_premium(
        self,
    ):
        self._text_employee(100, weekly_hours=2)
        records = self._records(self._text_report())
        self.assertEqual(records[2][13:18], ["11,00", "34,45", "0,00", "0,00", "45,45"])
        self.assertEqual(records[3][7:10], ["11,00", "5,00", "45,45"])
        self.assertEqual(records[3][15:17], ["0", "29,45"])

    def test_actual_full_month_pn_keeps_registered_count_without_paid_count(self):
        _employee, slip = self._text_employee(full_pn=True)
        self.assertEqual(
            slip.get_salary_line_total("GROSS"),
            0,
            slip.l10n_sk_health_assessment_snapshot,
        )
        self.assertEqual(
            slip.get_salary_line_total("HEALTHDOPLATOK"),
            0,
            slip.l10n_sk_health_assessment_snapshot,
        )
        self.assertEqual(slip.get_salary_line_total("SICK_COMP"), 680)
        records = self._records(self._text_report())
        self.assertEqual(records[2][0], "1")
        self.assertEqual(records[2][5:9], ["0", "0", "0", "0"])
        self.assertEqual(records[2][17], "0,00")

    def test_written_concurrent_optout_is_distinct_from_state_or_disability(self):
        self._text_employee(100, weekly_hours=2, minimum_opt_out=True)
        records = self._records(self._text_report())
        self.assertEqual(records[3][7:10], ["11,00", "5,00", "16,00"])
        self.assertEqual(records[3][15:17], ["1", "0,00"])

    def test_later_insurer_and_identity_edit_do_not_reclassify_the_old_source(self):
        employee, _slip = self._text_employee()
        employee.write(
            {"l10n_sk_health_insurer_code": "25", "identification_id": "9002022345"}
        )
        report = self._text_report()
        records = self._records(report)
        self.assertEqual(records[3][1], "8501011234")
        self.assertEqual(records[0][4], "2400")

    def test_corrective_native_workflow_preserves_exact_filed_bytes(self):
        self._text_employee()
        original = self._text_report()
        self._records(original)
        original.action_submit()
        attachment = original.submitted_attachment_id
        original_bytes = attachment.datas
        correction = original.copy(
            {"correction_type": "corrective", "batch_sequence": 2}
        )
        self.assertEqual(correction.state, "draft")
        records = self._records(correction)
        self.assertEqual(records[0][0], "O")
        self.assertEqual(correction.xml_attachment_id.name, "O5142606.002")
        self.company.name = "Changed current address book name"
        self.assertEqual(attachment.datas, original_bytes)
        self.assertIn(attachment, original.filed_history_ids)
        with self.assertRaises(UserError):
            original.registered_count = 99

    def test_missing_registration_review_or_foreign_bank_is_not_silently_accepted(self):
        self._text_employee()
        report = self._text_report(registered_count=-1)
        with self.assertRaises(UserError):
            report.action_generate()

        report.registered_count = 1
        outsider = self.env["res.partner"].create({"name": "Unrelated company"})
        report.payment_bank_id = self.env["res.partner.bank"].create(
            {"partner_id": outsider.id, "acc_number": "SK3112000000198742637541"}
        )
        with self.assertRaises(UserError):
            report.action_generate()

    def test_text_payer_number_is_independent_of_the_company_legacy_default(self):
        self._text_employee()
        self.company.l10n_sk_health_payer_number = False
        records = self._records(self._text_report())
        self.assertEqual(records[0][3], "9900112233")
