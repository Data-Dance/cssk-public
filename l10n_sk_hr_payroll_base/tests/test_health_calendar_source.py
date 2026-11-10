# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHealthCalendarSource(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Synthetic health calendar",
                "company_id": cls.env.company.id,
            }
        )

    def calendar(self, rows=None, **extra):
        values = {
            "employee_id": self.employee.id,
            "company_id": self.env.company.id,
            "month": "2026-06-01",
            "evidence": "Synthetic reviewed work and notice source",
            "complete": True,
            "interval_ids": [
                Command.create(
                    {
                        "kind": kind,
                        "date_start": start,
                        "date_end": end,
                    }
                )
                for kind, start, end in (rows or [])
            ],
        }
        values.update(extra)
        return self.env["l10n.sk.health.calendar"].create(values)

    def test_actual_agreement_days_feed_the_shared_context(self):
        row = self.calendar(
            [
                ("2D", "2026-06-02", "2026-06-02"),
                ("2D", "2026-06-12", "2026-06-12"),
            ]
        )
        row.action_review()
        facts = row._calendar_context()
        self.assertEqual(facts["insured_days"], 2)
        self.assertEqual(facts["op_employment_days"], 0)
        self.assertEqual(facts["calendar_id"], row.id)
        self.assertEqual(row.reviewed_by, self.env.user)
        self.assertTrue(row.reviewed_at)

    def test_empty_calendar_needs_explicit_complete_review(self):
        row = self.calendar(complete=False)
        with self.assertRaises(UserError):
            row.action_review()
        row.complete = True
        row.evidence = " "
        with self.assertRaises(UserError):
            row.action_review()
        row.evidence = "Synthetic zero-insured-day month reviewed"
        row.action_review()
        self.assertEqual(row._calendar_context()["insured_days"], 0)

    def test_source_dates_are_not_clamped_to_hide_a_wrong_month(self):
        for start, end, kind in [
            ("2026-05-31", "2026-06-02", "2D"),
            ("2026-06-01", "2026-07-01", "2"),
            ("2026-06-03", "2026-06-02", "2D"),
            ("2026-06-01", "2026-06-02", "2Y"),
        ]:
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                self.calendar([(kind, start, end)])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.calendar(month="2026-06-02")

    def test_parent_month_change_rechecks_existing_intervals(self):
        row = self.calendar([("2", "2026-06-01", "2026-06-30")])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            row.month = date(2026, 7, 1)

    def test_reviewed_parent_and_all_child_paths_are_immutable(self):
        row = self.calendar([("2D", "2026-06-02", "2026-06-02")])
        row.action_review()
        for operation in [
            lambda: row.write({"evidence": "changed"}),
            lambda: row.unlink(),
            lambda: row.interval_ids.write({"date_end": "2026-06-03"}),
            lambda: row.interval_ids.unlink(),
            lambda: self.env["l10n.sk.health.calendar.interval"]
            .with_context(
                default_calendar_id=row.id,
            )
            .create(
                {"kind": "2D", "date_start": "2026-06-03", "date_end": "2026-06-03"}
            ),
        ]:
            with self.assertRaises(UserError):
                operation()

    def test_moving_a_draft_child_into_a_reviewed_parent_is_rejected(self):
        row = self.calendar()
        row.action_review()
        draft = self.calendar([("2D", "2026-07-02", "2026-07-02")], month="2026-07-01")
        with self.assertRaises(UserError):
            draft.interval_ids.calendar_id = row

    def test_generated_review_fields_reject_api_values_and_context_defaults(self):
        for key, value in [
            ("state", "reviewed"),
            ("reviewed_by", self.env.uid),
            ("reviewed_at", "2026-06-01 00:00:00"),
            ("supersedes_id", False),
        ]:
            with self.assertRaises(UserError):
                self.calendar(**{key: value})
            with self.assertRaises(UserError):
                self.env["l10n.sk.health.calendar"].with_context(
                    **{
                        "default_" + key: value,
                    }
                ).create({})

    def test_revision_preserves_original_facts_and_requires_a_new_review(self):
        original = self.calendar([("2D", "2026-06-02", "2026-06-02")])
        original.action_review()
        facts, reviewer, at = (
            original._calendar_context(),
            original.reviewed_by,
            original.reviewed_at,
        )
        action = original.action_create_revision()
        revision = self.env["l10n.sk.health.calendar"].browse(action["res_id"])
        self.assertEqual(original.state, "superseded")
        self.assertEqual(original._calendar_context(), facts)
        self.assertEqual((original.reviewed_by, original.reviewed_at), (reviewer, at))
        self.assertEqual(revision.supersedes_id, original)
        self.assertEqual(revision.state, "draft")
        self.assertFalse(revision.complete)
        self.assertFalse(revision.reviewed_by)
        revision.interval_ids.date_end = date(2026, 6, 3)
        revision.complete = True
        revision.action_review()
        self.assertEqual(revision._calendar_context()["insured_days"], 2)
        self.assertEqual(original._calendar_context()["insured_days"], 1)
        with self.assertRaises(UserError):
            original.action_create_revision()

    def test_foreign_employee_and_foreign_child_access_are_rejected(self):
        other = self.env["res.company"].create({"name": "Synthetic foreign calendar"})
        employee = self.env["hr.employee"].create(
            {"name": "Other", "company_id": other.id}
        )
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.calendar(employee_id=employee.id)
        foreign = self.calendar(
            [("2D", "2026-06-02", "2026-06-02")],
            company_id=other.id,
            employee_id=employee.id,
        )
        user = self.env["res.users"].create(
            {
                "name": "Synthetic calendar HR manager",
                "login": "synthetic-health-calendar-manager",
                "company_id": self.env.company.id,
                "company_ids": [Command.set(self.env.company.ids)],
                "group_ids": [Command.set(self.env.ref("hr.group_hr_manager").ids)],
            }
        )
        with self.assertRaises(AccessError):
            foreign.with_user(user).action_review()
        with self.assertRaises(AccessError):
            foreign.interval_ids.with_user(user).write({"date_end": "2026-06-03"})
