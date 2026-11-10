# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import closing

from psycopg2 import errors as pg_errors

from odoo import SUPERUSER_ID, Command, api
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHealthCalendarConcurrency(TransactionCase):
    def test_review_retries_after_another_transaction_changes_insured_days(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
            employee = env["hr.employee"].create(
                {
                    "name": "Synthetic health calendar concurrency",
                    "date_version": "2026-01-01",
                }
            )
            calendar = env["l10n.sk.health.calendar"].create(
                {
                    "company_id": employee.company_id.id,
                    "employee_id": employee.id,
                    "month": "2026-06-01",
                    "complete": True,
                    "evidence": "Synthetic reviewed actual days",
                    "interval_ids": [
                        Command.create(
                            {
                                "kind": "2D",
                                "date_start": "2026-06-01",
                                "date_end": "2026-06-02",
                            }
                        )
                    ],
                }
            )
            employee_id, calendar_id, interval_id = (
                employee.id,
                calendar.id,
                calendar.interval_ids.id,
            )
        try:
            with (
                closing(self.registry.cursor()) as old,
                closing(self.registry.cursor()) as fresh,
            ):
                stale = api.Environment(old, SUPERUSER_ID, {"lang": "en_US"})[
                    "l10n.sk.health.calendar"
                ].browse(calendar_id)
                self.assertEqual(stale._calendar_context()["insured_days"], 2)
                current = api.Environment(fresh, SUPERUSER_ID, {"lang": "en_US"})
                current["l10n.sk.health.calendar.interval"].browse(
                    interval_id
                ).date_end = "2026-06-01"
                fresh.commit()
                with self.assertRaises(pg_errors.SerializationFailure):
                    stale.action_review()
                old.rollback()
                refreshed = api.Environment(old, SUPERUSER_ID, {})[
                    "l10n.sk.health.calendar"
                ].browse(calendar_id)
                self.assertEqual(refreshed._calendar_context()["insured_days"], 1)
                old.rollback()
        finally:
            with self.registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                env["l10n.sk.health.calendar"].browse(calendar_id).unlink()
                env["hr.employee"].browse(employee_id).unlink()
