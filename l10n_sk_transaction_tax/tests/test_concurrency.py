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
class TestDftConcurrency(TransactionCase):
    def setUp(self):
        super().setUp()
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})
            company = env.company
            account = env["account.account"].create(
                {
                    "name": "Synthetic DFT concurrency",
                    "code": "345" + uuid4().hex[:8],
                    "account_type": "liability_current",
                    "company_ids": [Command.set(company.ids)],
                }
            )
            journal = env["account.journal"].create(
                {
                    "name": "Synthetic DFT concurrency",
                    "code": uuid4().hex[:5],
                    "type": "general",
                    "company_id": company.id,
                }
            )
            move = self._entry(env, account.id, journal.id)
            first = env["l10n.sk.transaction.tax"].create(
                {
                    "company_id": company.id,
                    "period": "2026-05-01",
                    "signed_on": "2026-06-30",
                    "filing_on": "2026-06-30",
                    "deadline": "2026-06-30",
                    "deadline_reference": "Synthetic concurrency calendar",
                    "representative_kind": "statutarnyZastupcaPO",
                    "representative_id": company.partner_id.id,
                    "source_ids": [
                        Command.create(
                            {
                                "move_line_id": move.line_ids[0].id,
                                "kind": "transfer",
                                "actual_on": "2026-05-20",
                                "source_reference": "Original synthetic source",
                                "reviewed": True,
                            }
                        )
                    ],
                }
            )
            second = first.copy(
                {
                    "period": "2026-06-01",
                    "signed_on": "2026-07-31",
                    "filing_on": "2026-07-31",
                    "deadline": "2026-07-31",
                    "source_ids": [],
                }
            )
            self.notice_ids, self.source_id = (first | second).ids, first.source_ids.id
            self.fixture_ids = (move.id, journal.id, account.id)
        self.addCleanup(self._drop)

    def _entry(self, env, account_id, journal_id):
        return env["account.move"].create(
            {
                "journal_id": journal_id,
                "date": "2026-05-20",
                "line_ids": [
                    Command.create(
                        {
                            "name": "Synthetic debit",
                            "account_id": account_id,
                            "debit": 100,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Synthetic credit",
                            "account_id": account_id,
                            "credit": 100,
                        }
                    ),
                ],
            }
        )

    def _drop(self):
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            env["l10n.sk.transaction.tax"].browse(self.notice_ids).unlink()
            for model, identifier in zip(
                ("account.move", "account.journal", "account.account"), self.fixture_ids
            ):
                env[model].browse(identifier).unlink()

    def _env(self, cr):
        return api.Environment(cr, SUPERUSER_ID, {"lang": "en_US"})

    def test_committed_source_change_retries_a_stale_compute(self):
        with (
            closing(self.registry.cursor()) as old,
            closing(self.registry.cursor()) as fresh,
        ):
            stale = self._env(old)["l10n.sk.transaction.tax"].browse(self.notice_ids[0])
            self.assertEqual(
                stale.source_ids.source_reference, "Original synthetic source"
            )
            self._env(fresh)["l10n.sk.transaction.tax.source"].browse(
                self.source_id
            ).source_reference = "Changed synthetic source"
            fresh.commit()
            with self.assertRaises(pg_errors.SerializationFailure):
                stale.action_compute_lines()
            old.rollback()
            self.assertEqual(
                self._env(old)["l10n.sk.transaction.tax.source"]
                .browse(self.source_id)
                .source_reference,
                "Changed synthetic source",
            )
            old.rollback()

    def test_a_different_month_cannot_use_an_old_company_allocation_snapshot(self):
        with (
            closing(self.registry.cursor()) as old,
            closing(self.registry.cursor()) as fresh,
        ):
            stale = self._env(old)["l10n.sk.transaction.tax"].browse(self.notice_ids[1])
            self.assertEqual(str(stale.period), "2026-06-01")
            self._env(fresh)["l10n.sk.transaction.tax"].browse(
                self.notice_ids[0]
            )._lock()
            fresh.commit()
            with self.assertRaises(pg_errors.SerializationFailure):
                stale._lock()
            old.rollback()

    def test_busy_company_allocation_is_refused_without_a_deadlock(self):
        with (
            closing(self.registry.cursor()) as first,
            closing(self.registry.cursor()) as other,
        ):
            self._env(first)["l10n.sk.transaction.tax"].browse(
                self.notice_ids[0]
            )._lock()
            with self.assertRaisesRegex(UserError, "Another process"):
                self._env(other)["l10n.sk.transaction.tax"].browse(
                    self.notice_ids[1]
                )._lock()
            other.rollback()
            first.rollback()

    def test_native_accounting_company_fk_does_not_block_non_key_dft_coordinator(self):
        with (
            closing(self.registry.cursor()) as accounting,
            closing(self.registry.cursor()) as tax,
        ):
            env = self._env(accounting)
            self._entry(env, self.fixture_ids[2], self.fixture_ids[1])
            env.flush_all()
            accounting.execute("SET CONSTRAINTS ALL IMMEDIATE")
            # The native entry retains company FK/key-share locks until commit.
            self._env(tax)["l10n.sk.transaction.tax"].browse(self.notice_ids[0])._lock()
            tax.rollback()
            accounting.rollback()
