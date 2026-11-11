# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import closing
from uuid import uuid4

from psycopg2 import errors as pg_errors

from odoo import SUPERUSER_ID, Command, api
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestConcurrentWithholding(TransactionCase):
    """Real committed child changes must invalidate an older export snapshot."""

    def setUp(self):
        super().setUp()
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
            company = env.company
            account = env["account.account"].create(
                {
                    "name": "Synthetic4311 concurrency account",
                    "code": "342" + uuid4().hex[:8],
                    "account_type": "liability_current",
                    "company_ids": [Command.set(company.ids)],
                }
            )
            journal = env["account.journal"].create(
                {
                    "name": "Synthetic4311 concurrency",
                    "code": uuid4().hex[:5],
                    "type": "general",
                    "company_id": company.id,
                }
            )
            move = env["account.move"].create(
                {
                    "company_id": company.id,
                    "journal_id": journal.id,
                    "date": "2026-05-20",
                    "line_ids": [
                        Command.create({"account_id": account.id, "debit": 100}),
                        Command.create({"account_id": account.id, "credit": 100}),
                    ],
                }
            )
            notice = env["l10n.sk.withholding"].create(
                {
                    "company_id": company.id,
                    "period": "2026-05-01",
                    "prepared_by": "Synthetic concurrency",
                    "prepared_on": "2026-06-15",
                    "filing_on": "2026-06-15",
                    "tax_account_id": account.id,
                    "event_ids": [
                        Command.create(
                            {
                                "partner_id": company.partner_id.id,
                                "first_name": "Synthetic",
                                "last_name": "Concurrent",
                                "gross": 100,
                                "decision_on": "2026-05-10",
                                "paid_on": "2026-05-20",
                                "distribution_line_id": move.line_ids[0].id,
                                "payment_line_id": move.line_ids[1].id,
                                "source_reference": "Synthetic concurrency test only",
                            }
                        )
                    ],
                }
            )
            self.notice_id, self.event_id = notice.id, notice.event_ids.id
            self.other_notice_id = notice.copy(
                {"period": "2026-06-01", "event_ids": []}
            ).id
            self.cleanup_ids = (move.id, journal.id, account.id)
        self.addCleanup(self._drop_fixture)

    def _drop_fixture(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env["l10n.sk.withholding"].search(
                [("original_return_id", "in", [self.notice_id, self.other_notice_id])]
            ).unlink()
            env["l10n.sk.withholding"].browse(
                [self.notice_id, self.other_notice_id]
            ).unlink()
            for model, identifier in zip(
                ("account.move", "account.journal", "account.account"), self.cleanup_ids
            ):
                env[model].browse(identifier).unlink()

    def test_committed_income_change_forces_stale_export_transaction_to_retry(self):
        with (
            closing(self.registry.cursor()) as old,
            closing(self.registry.cursor()) as fresh,
        ):
            old_env = api.Environment(old, SUPERUSER_ID, {"lang": "en_US"})
            fresh_env = api.Environment(fresh, SUPERUSER_ID, {"lang": "en_US"})
            notice = old_env["l10n.sk.withholding"].browse(self.notice_id)
            self.assertEqual(notice.event_ids.gross, 100)
            fresh_env["l10n.sk.withholding.event"].browse(self.event_id).write(
                {"gross": 200}
            )
            fresh.commit()
            # Cache invalidation alone cannot replace a REPEATABLE READ snapshot.
            with self.assertRaises(pg_errors.SerializationFailure):
                notice._lock()
            old.rollback()
            refreshed = api.Environment(old, SUPERUSER_ID, {})[
                "l10n.sk.withholding"
            ].browse(self.notice_id)
            self.assertEqual(refreshed.event_ids.gross, 200)

    def test_other_month_change_invalidates_a_stale_company_allocation(self):
        with (
            closing(self.registry.cursor()) as old,
            closing(self.registry.cursor()) as fresh,
        ):
            stale = api.Environment(old, SUPERUSER_ID, {"lang": "en_US"})[
                "l10n.sk.withholding"
            ].browse(self.notice_id)
            self.assertEqual(stale.event_ids.gross, 100)
            other = api.Environment(fresh, SUPERUSER_ID, {"lang": "en_US"})[
                "l10n.sk.withholding"
            ].browse(self.other_notice_id)
            other.write({"prepared_by": "Changed other month reservation"})
            fresh.commit()
            with self.assertRaises(pg_errors.SerializationFailure):
                stale._lock()
            old.rollback()

    def test_different_months_share_one_company_allocation_lock(self):
        with (
            closing(self.registry.cursor()) as first,
            closing(self.registry.cursor()) as other,
        ):
            api.Environment(first, SUPERUSER_ID, {"lang": "en_US"})[
                "l10n.sk.withholding"
            ].browse(self.notice_id)._lock()
            with self.assertRaisesRegex(UserError, "Another process"):
                api.Environment(other, SUPERUSER_ID, {"lang": "en_US"})[
                    "l10n.sk.withholding"
                ].browse(self.other_notice_id)._lock()
            other.rollback()
            first.rollback()

    def test_busy_notice_is_refused_without_waiting_on_deferred_child_fks(self):
        with (
            closing(self.registry.cursor()) as first,
            closing(self.registry.cursor()) as other,
        ):
            api.Environment(first, SUPERUSER_ID, {})["l10n.sk.withholding"].browse(
                self.notice_id
            )._lock()
            with self.assertRaisesRegex(UserError, "Another process"):
                api.Environment(other, SUPERUSER_ID, {"lang": "en_US"})[
                    "l10n.sk.withholding"
                ].browse(self.notice_id)._lock()
            first.rollback()
            other.rollback()

    def test_new_correction_advances_shared_ancestor_before_inserting_its_fk(self):
        with (
            closing(self.registry.cursor()) as old,
            closing(self.registry.cursor()) as fresh,
        ):
            stale = api.Environment(old, SUPERUSER_ID, {})[
                "l10n.sk.withholding"
            ].browse(self.notice_id)
            self.assertEqual(stale.prepared_by, "Synthetic concurrency")
            current = api.Environment(fresh, SUPERUSER_ID, {})[
                "l10n.sk.withholding"
            ].browse(self.notice_id)
            current.copy({"original_return_id": current.id, "event_ids": []})
            fresh.commit()
            with self.assertRaises(pg_errors.SerializationFailure):
                stale._lock()
            old.rollback()
