# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import closing

from psycopg2 import errors as pg_errors

from odoo import SUPERUSER_ID, Command, api
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRegistrationConcurrency(TransactionCase):
    def test_committed_event_edit_forces_stale_generator_to_retry(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
            company = env["res.company"].create(
                {
                    "name": "Synthetic601 concurrency only",
                    "country_id": env.ref("base.sk").id,
                }
            )
            employee = env["hr.employee"].create(
                {"name": "Synthetic601 person", "company_id": company.id}
            )
            bank = env["res.partner.bank"].create(
                {
                    "partner_id": company.partner_id.id,
                    "acc_number": "SK3112000000198742637541",
                }
            )
            batch = (
                env["l10n.sk.health.registration"]
                .with_company(company)
                .create(
                    {
                        "company_id": company.id,
                        "year": "2026",
                        "month": "6",
                        "insurer_code": "25",
                        "sending_date": "2026-07-01",
                        "receiver_ico": "12345678",
                        "payer_number": "9900112233",
                        "payment_bank_id": bank.id,
                        "responsible_person": "Synthetic concurrency",
                        "phone": "0900000000",
                        "event_ids": [
                            Command.create(
                                {
                                    "employee_id": employee.id,
                                    "first_name": "Synthetic",
                                    "last_name": "Person",
                                    "birth_number": "005101123",
                                    "code": "2D",
                                    "validity": "Z",
                                    "changed_on": "2026-06-02",
                                    "source_reference": "Synthetic601 actual work day",
                                    "employer_notice_reviewed": True,
                                }
                            )
                        ],
                    }
                )
            )
            company_id, employee_id, bank_id, batch_id, event_id = (
                company.id,
                employee.id,
                bank.id,
                batch.id,
                batch.event_ids.id,
            )
        try:
            with (
                closing(self.registry.cursor()) as old,
                closing(self.registry.cursor()) as fresh,
            ):
                old_env = api.Environment(old, SUPERUSER_ID, {"lang": "en_US"})
                batch = old_env["l10n.sk.health.registration"].browse(batch_id)
                self.assertEqual(batch.event_ids.first_name, "Synthetic")
                api.Environment(fresh, SUPERUSER_ID, {})[
                    "l10n.sk.health.registration.event"
                ].browse(event_id).first_name = "Changed"
                fresh.commit()
                with self.assertRaises(pg_errors.SerializationFailure):
                    batch._lock_for_change()
                old.rollback()
                self.assertEqual(
                    api.Environment(old, SUPERUSER_ID, {})[batch._name]
                    .browse(batch_id)
                    .event_ids.first_name,
                    "Changed",
                )
                old.rollback()
        finally:
            with self.registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env["l10n.sk.health.registration"].browse(batch_id).unlink()
                env["hr.employee"].browse(employee_id).unlink()
                env["res.partner.bank"].browse(bank_id).unlink()
                env["res.company"].browse(company_id).unlink()
