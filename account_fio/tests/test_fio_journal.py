# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account_fio_base.tests.fio_fixtures import statement_xml

from .common import TOKEN_READ, FioCommon


@tagged("post_install", "-at_install")
class TestFioJournal(FioCommon):
    def test_tokens_are_administrator_only(self):
        """Fio carries the token in the URL path; accountants must not see it."""
        fields_def = self.env["account.journal"]._fields
        self.assertEqual(fields_def["fio_token_read"].groups, "base.group_system")
        self.assertEqual(fields_def["fio_token_write"].groups, "base.group_system")
        # ...but everybody may see whether one is configured.
        self.assertFalse(fields_def["fio_has_token_read"].groups)
        self.assertTrue(self.journal.fio_has_token_read)

    def test_truncated_token_is_refused(self):
        with self.assertRaises(ValidationError):
            self.journal.sudo().write({"fio_token_read": "short"})

    def test_test_connection_records_what_the_bank_says(self):
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            return_value=statement_xml(),
        ):
            self.journal.action_fio_test_connection()
        self.assertEqual(self.journal.fio_account_number, "2111111111")
        self.assertEqual(self.journal.fio_iban, "CZ8020100000002111111111")

    def test_a_rejected_token_reaches_the_user_as_a_message(self):
        """FioError is a plain Exception, so an unwrapped one leaves the button
        showing a bare "Internal server error" — losing the only diagnosis the
        user gets. Found on DURWEN staging with a stale token."""
        from odoo.addons.account_fio_base.utils.client import FioError

        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            side_effect=FioError(
                "Fio rejected the token as unknown, expired or inactive"
            ),
        ), self.assertRaises(UserError) as caught:
            self.journal.action_fio_test_connection()
        self.assertIn("expired or inactive", str(caught.exception))

    def test_test_connection_does_not_show_the_token_in_its_error(self):
        """The READ endpoints carry the token in the URL PATH, so a transport
        failure built from that URL can quote the credential. FioClient masks
        what it raises, so this asserts the SECOND layer: the sink must not
        depend on the client having done it, nor on this handler's ``except``
        clause staying narrower than ``Exception``. The FioError below is
        deliberately unmasked, standing in for one that arrived that way."""
        from odoo.addons.account_fio_base.utils.client import FioError

        leaky = (
            "HTTPSConnectionPool(host='fioapi.fio.cz'): /ib_api/rest/periods/"
            "%s/2026-01-01/2026-01-01/transactions.xml" % TOKEN_READ
        )
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            side_effect=FioError(leaky),
        ), self.assertRaises(UserError) as caught:
            self.journal.action_fio_test_connection()
        self.assertNotIn(TOKEN_READ, str(caught.exception))
        self.assertIn("***", str(caught.exception))

    def test_a_token_for_another_account_is_refused(self):
        """One token serves one account (§2); pointing it at the wrong journal
        would import somebody else's movements into these books."""
        payload = statement_xml(info={"iban": "CZ4020100000009999999999",
                                      "accountId": "9999999999"})
        with patch.object(
            type(self.journal), "_fio_call", autospec=True, return_value=payload,
        ), self.assertRaises(UserError) as caught:
            self.journal.action_fio_test_connection()
        self.assertIn("serves one account", str(caught.exception))

    def test_throttle_refuses_to_block_a_user_for_a_full_interval(self):
        self.journal.sudo().fio_last_read_at = fields.Datetime.now()
        with self.assertRaises(UserError) as caught:
            self.journal._fio_wait_for_slot("read", interactive=True)
        self.assertIn("30 seconds", str(caught.exception))

    def test_throttle_is_silent_once_the_interval_has_passed(self):
        self.journal.sudo().fio_last_read_at = fields.Datetime.now() - timedelta(seconds=60)
        self.journal._fio_wait_for_slot("read", interactive=True)  # no exception

    def test_expiry_raises_an_activity(self):
        self.journal.sudo().fio_token_read_expiry = (
            fields.Date.context_today(self.journal) + timedelta(days=3)
        )
        self.env["account.journal"]._fio_cron_check_token_expiry()
        self.assertTrue(self.journal.activity_ids)

    def test_expiry_does_not_pile_up_activities(self):
        self.journal.sudo().fio_token_read_expiry = (
            fields.Date.context_today(self.journal) + timedelta(days=3)
        )
        self.env["account.journal"]._fio_cron_check_token_expiry()
        self.env["account.journal"]._fio_cron_check_token_expiry()
        self.assertEqual(len(self.journal.activity_ids), 1)

    def test_what_the_bank_reports_is_recorded_on_the_journal(self):
        """The journal already has a name; what the old connection record added
        to it was the account number Fio reports, which is a field of its own."""
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            return_value=statement_xml(),
        ):
            self.journal.action_fio_test_connection()
        self.assertEqual(self.journal.fio_account_number, "2111111111")
        self.assertEqual(self.journal.fio_bank_code, "2010")

    def test_a_token_for_an_account_in_another_currency_is_refused(self):
        payload = statement_xml(info={"currency": "EUR"})
        with patch.object(
            type(self.journal), "_fio_call", autospec=True, return_value=payload,
        ), self.assertRaises(UserError) as caught:
            self.journal.action_fio_test_connection()
        self.assertIn("EUR", str(caught.exception))

    def test_a_journal_without_a_bank_account_skips_the_comparison(self):
        """Nothing to compare against is not the same as a mismatch."""
        journal = self.env["account.journal"].sudo().create({
            "name": "Fio bare", "type": "bank", "code": "FIOBA",
            "company_id": self.company.id,
            "currency_id": self.czk.id,
            "fio_token_read": "d" * 64,
        })
        with patch.object(
            type(journal), "_fio_call", autospec=True, return_value=statement_xml(),
        ):
            journal.action_fio_test_connection()  # no exception
        self.assertEqual(journal.fio_account_number, "2111111111")

    def test_the_call_stamps_the_token_it_used(self):
        with patch.object(
            type(self.journal), "_fio_call", autospec=True, return_value=statement_xml(),
        ):
            self.journal._fio_stamp("read")
        self.assertTrue(self.journal.fio_last_read_at)
        self.assertFalse(self.journal.fio_last_write_at)

    def test_the_two_tokens_have_independent_budgets(self):
        """Splitting read from submit doubles the effective rate budget."""
        self.journal.sudo().fio_last_read_at = fields.Datetime.now()
        with self.assertRaises(UserError):
            self.journal._fio_wait_for_slot("read", interactive=True)
        self.journal._fio_wait_for_slot("write", interactive=True)  # untouched

    def test_a_missing_submit_token_says_which_right_to_ask_for(self):
        self.journal.sudo().fio_token_write = False
        with self.assertRaises(UserError) as caught:
            self.journal._fio_token("write")
        self.assertIn("zadávání platebních", str(caught.exception))

    def test_a_missing_read_token(self):
        self.journal.sudo().fio_token_read = False
        with self.assertRaises(UserError):
            self.journal._fio_token("read")

    def test_a_journal_without_a_token_is_not_a_fio_journal(self):
        """``fio_has_token_read`` is what the menu, the cron and the pull all
        key on, so it has to be false for an ordinary bank journal and true as
        soon as a token is pasted in."""
        journal = self.env["account.journal"].sudo().create({
            "name": "Fio none", "type": "bank", "code": "FIONO",
            "company_id": self.company.id,
        })
        self.assertFalse(journal.fio_has_token_read)
        self.assertFalse(journal.fio_has_token_write)
        journal.fio_token_read = "e" * 64
        self.assertTrue(journal.fio_has_token_read)
        self.assertFalse(journal.fio_has_token_write)

    def test_the_token_flags_are_stored_so_they_can_be_searched(self):
        """The Fio journal list and both crons filter on them; a non-stored
        compute could not be expressed as a domain at all."""
        for name in ("fio_has_token_read", "fio_has_token_write"):
            self.assertTrue(
                self.env["account.journal"]._fields[name].store, name,
            )
        found = self.env["account.journal"].search([
            ("fio_has_token_read", "=", True),
        ])
        self.assertIn(self.journal, found)

    def test_the_lock_does_not_pin_the_journal_row(self):
        """An advisory lock, not SELECT ... FOR UPDATE. The row lock would hold
        a core account_journal row for the length of Fio's 30-second call
        floor, once an hour from the cron, and every unrelated write to that
        journal would block behind it for reasons nothing in the UI explains."""
        self.journal._fio_lock()
        self.env.cr.execute(
            "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' "
            "AND pid = pg_backend_pid()"
        )
        self.assertGreaterEqual(self.env.cr.fetchone()[0], 1)
        # Re-entrant within the transaction: a pull that calls twice must not
        # deadlock against itself.
        self.journal._fio_lock()

    def test_the_expiry_activity_goes_to_a_human(self):
        self.journal.sudo().fio_token_read_expiry = (
            fields.Date.context_today(self.journal) + timedelta(days=3)
        )
        self.env["account.journal"]._fio_cron_check_token_expiry()
        assignee = self.journal.activity_ids.user_id
        self.assertTrue(assignee)
        self.assertFalse(assignee.share)

    def test_both_tokens_are_watched_separately(self):
        today = fields.Date.context_today(self.journal)
        self.journal.sudo().write({
            "fio_token_read_expiry": today + timedelta(days=3),
            "fio_token_write_expiry": today + timedelta(days=5),
        })
        self.env["account.journal"]._fio_cron_check_token_expiry()
        self.assertEqual(len(self.journal.activity_ids), 2)

    def test_a_distant_expiry_is_left_alone(self):
        self.journal.sudo().fio_token_read_expiry = (
            fields.Date.context_today(self.journal) + timedelta(days=120)
        )
        self.env["account.journal"]._fio_cron_check_token_expiry()
        self.assertFalse(self.journal.activity_ids)
