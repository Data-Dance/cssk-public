# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import contextmanager
from uuid import uuid4

from psycopg2.errors import SerializationFailure

from odoo import SUPERUSER_ID, api, sql_db
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSocialSource(TransactionCase):
    @contextmanager
    def source_fixture(self, payslip=True):
        connection = sql_db.db_connect(self.env.cr.dbname)
        company_id = employee_id = slip_id = False
        try:
            with connection.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
                company = env["res.company"].create(
                    {
                        "name": "Social source concurrency " + uuid4().hex,
                        "country_id": env.ref("base.sk").id,
                        "currency_id": env.ref("base.EUR").id,
                    }
                )
                env.user.company_ids |= company
                env = env(context=dict(env.context, allowed_company_ids=company.ids))
                structure = env.ref(
                    "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
                )
                employee = env["hr.employee"].create(
                    {
                        "name": company.name,
                        "company_id": company.id,
                        "date_version": "2026-01-01",
                        "contract_date_start": "2026-01-01",
                        "wage": 2000,
                        "struct_id": structure.id,
                        "l10n_sk_tax_declaration_signed": False,
                    }
                )
                version = employee.version_id
                company_id, employee_id = company.id, employee.id
                if payslip:
                    slip = env["hr.payslip"].create(
                        self.slip_values(employee, version, structure)
                    )
                    slip.compute_sheet()
                    slip_id = slip.id
                version_id, structure_id = version.id, structure.id
                cr.commit()
            yield connection, company_id, employee_id, version_id, structure_id, slip_id
        finally:
            if company_id:
                with connection.cursor() as cr:
                    env = api.Environment(
                        cr,
                        SUPERUSER_ID,
                        {"lang": "en_US", "allowed_company_ids": [company_id]},
                    )
                    if slip_id:
                        slip = env["hr.payslip"].browse(slip_id).exists()
                        if slip and slip.state not in ("draft", "cancel"):
                            slip.action_payslip_draft()
                        slip.unlink()
                    env["hr.employee"].browse(employee_id).exists().unlink()
                    env["res.company"].browse(company_id).exists().unlink()
                    cr.commit()

    @staticmethod
    def slip_values(employee, version, structure):
        return {
            "name": "Social source concurrency",
            "employee_id": employee.id,
            "company_id": employee.company_id.id,
            "contract_id": version.id,
            "struct_id": structure.id,
            "date_from": "2026-03-01",
            "date_to": "2026-03-31",
        }

    def test_concurrent_version_change_retries_before_confirmation_then_rejects_stale(
        self,
    ):
        with self.source_fixture() as (
            connection,
            company,
            _employee,
            version,
            _structure,
            slip,
        ):
            with connection.cursor() as stale, connection.cursor() as writer:
                context = {"allowed_company_ids": [company], "lang": "en_US"}
                old_env = api.Environment(stale, SUPERUSER_ID, context)
                new_env = api.Environment(writer, SUPERUSER_ID, context)
                self.assertTrue(
                    old_env["hr.payslip"].browse(slip).l10n_sk_social_assessment
                )
                new_env["hr.version"].browse(version).wage = 2200
                writer.commit()
                with self.assertRaises(SerializationFailure):
                    old_env["hr.payslip"].browse(slip).with_context(
                        without_compute_sheet=True
                    ).action_payslip_done()
                stale.rollback()
            with connection.cursor() as retry:
                env = api.Environment(retry, SUPERUSER_ID, context)
                with self.assertRaisesRegex(UserError, "sources changed"):
                    env["hr.payslip"].browse(slip).with_context(
                        without_compute_sheet=True
                    ).action_payslip_done()
                self.assertNotEqual(env["hr.payslip"].browse(slip).state, "done")

    def test_concurrent_version_insert_retries_the_old_employee_snapshot(self):
        with self.source_fixture(payslip=False) as (
            connection,
            company,
            employee,
            version,
            _structure,
            _slip,
        ):
            context = {"allowed_company_ids": [company], "lang": "en_US"}
            with connection.cursor() as stale, connection.cursor() as writer:
                old_env = api.Environment(stale, SUPERUSER_ID, context)
                new_env = api.Environment(writer, SUPERUSER_ID, context)
                self.assertEqual(old_env["hr.employee"].browse(employee).wage, 2000)
                new_env["hr.version"].browse(version).copy(
                    {"date_version": "2026-03-16", "wage": 2200}
                )
                writer.commit()
                with self.assertRaises(SerializationFailure):
                    old_env["hr.employee"].browse(
                        employee
                    )._l10n_sk_lock_social_source()
                stale.rollback()

    def test_employee_source_lock_is_compatible_with_actual_payslip_foreign_keys(self):
        with self.source_fixture(payslip=False) as (
            connection,
            company,
            employee,
            version,
            structure,
            _slip,
        ):
            context = {"allowed_company_ids": [company], "lang": "en_US"}
            with connection.cursor() as child, connection.cursor() as coordinator:
                env = api.Environment(child, SUPERUSER_ID, context)
                env["hr.payslip"].create(
                    self.slip_values(
                        env["hr.employee"].browse(employee),
                        env["hr.version"].browse(version),
                        env["hr.payroll.structure"].browse(structure),
                    )
                )
                child.execute("SET CONSTRAINTS ALL IMMEDIATE")
                coordinator.execute("SET LOCAL lock_timeout='1s'")
                other = api.Environment(coordinator, SUPERUSER_ID, context)
                other["hr.employee"].browse(employee)._l10n_sk_lock_social_source()
                coordinator.commit()
                child.rollback()
