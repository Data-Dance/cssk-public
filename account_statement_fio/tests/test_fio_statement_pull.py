# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account_fio.tests.common import FioCommon
from odoo.addons.account_fio_base.tests.fio_fixtures import (
    movement,
    statement_xml,
)


@tagged("post_install", "-at_install")
class TestFioStatementPull(FioCommon):
    def setUp(self):
        super().setUp()
        # The scheduled pull keys on the bank feed, so a journal under test is
        # one whose feed is Fio.
        self.journal.sudo().bank_statements_source = "fio"

    def _pull(self, payload, method="fio_pull", **kwargs):
        """Run a pull with the transport replaced by a canned payload."""
        with patch.object(
            type(self.journal), "_fio_call", return_value=payload, autospec=True,
        ):
            return getattr(self.journal, method)(**kwargs)

    # ------------------------------------------------------------------
    # mapping
    # ------------------------------------------------------------------

    def test_movement_becomes_a_statement_line(self):
        lines = self._pull(statement_xml([movement(
            movement_id=1147608196,
            date="2026-04-27+02:00",
            amount="-1234.50",
            columns={
                2: "2222233333", 3: "2010", 4: "0558", 5: "1234567890",
                10: "Dodavatel s.r.o.", 16: "Faktura 2026/0042",
                8: "Platba převodem uvnitř banky", 17: 2102392862,
                27: "END2END-1",
            },
        )]))
        self.assertEqual(len(lines), 1)
        line = lines
        self.assertEqual(line.date, date(2026, 4, 27))
        self.assertEqual(line.amount, -1234.50)
        self.assertEqual(line.partner_name, "Dodavatel s.r.o.")
        # account_statement_import_base sanitizes the number on the way in, so
        # that "2222233333/2010" and "22222333332010" are one account. The
        # unsanitized form is what Fio sent, not what Odoo stores.
        self.assertEqual(line.account_number, "22222333332010")
        self.assertEqual(line.transaction_type, "Platba převodem uvnitř banky")
        self.assertEqual(line.fio_movement_id, "1147608196")
        self.assertEqual(line.fio_instruction_id, "2102392862")
        self.assertEqual(line.ref, "END2END-1")
        self.assertIn("Faktura 2026/0042", line.payment_ref)
        self.assertIn("VS:1234567890", line.payment_ref)
        self.assertIn("KS:0558", line.payment_ref)

    def test_label_falls_back_through_the_columns(self):
        """Fio fills whichever text column the movement type happens to use."""
        lines = self._pull(statement_xml([
            movement(movement_id=1, columns={25: "Můj komentář"}),
            movement(movement_id=2, columns={7: "Nákup: PENNY MARKET s.r.o."}),
            movement(movement_id=3, columns={8: "Připsaný úrok"}),
        ]))
        labels = sorted(lines.mapped("payment_ref"))
        self.assertEqual(labels, [
            "Můj komentář",
            "Nákup: PENNY MARKET s.r.o.",
            "Připsaný úrok",
        ])

    def test_raw_payload_is_kept(self):
        lines = self._pull(statement_xml([movement()]))
        self.assertIn("movement_id", lines.raw_data)

    # ------------------------------------------------------------------
    # duplicates
    # ------------------------------------------------------------------

    def test_a_second_pull_imports_nothing(self):
        """The overlap window re-reads days on purpose; it must cost nothing."""
        payload = statement_xml([movement(movement_id=42)])
        first = self._pull(payload)
        second = self._pull(payload)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)

    def test_import_key_is_scoped_to_the_journal(self):
        self._pull(statement_xml([movement(movement_id=42)]))
        line = self.env["account.bank.statement.line"].search(
            [("fio_movement_id", "=", "42")]
        )
        self.assertIn(str(self.journal.id), line.unique_import_id)
        self.assertIn("fio-42", line.unique_import_id)

    def test_a_reversal_is_not_swallowed(self):
        """§5.3: storno keeps the instruction id and takes a new movement id."""
        lines = self._pull(statement_xml([
            movement(movement_id=1, amount="100.00", columns={17: 555}),
            movement(movement_id=2, amount="-100.00", columns={17: 555}),
        ]))
        self.assertEqual(len(lines), 2)
        self.assertEqual(sum(lines.mapped("amount")), 0)

    # ------------------------------------------------------------------
    # partner matching
    # ------------------------------------------------------------------

    def test_known_counterparty_is_matched(self):
        """``FioCommon`` already gives the supplier 2222233333/2010."""
        lines = self._pull(statement_xml([movement(
            columns={2: "2222233333", 3: "2010"},
        )]))
        self.assertEqual(lines.partner_id, self.supplier)
        self.assertEqual(lines.account_number, "22222333332010")
        # Not partner_bank_id: account.bank.statement.line inherits
        # account.move, whose _compute_partner_bank_id depends on partner_id and
        # reassigns the field from bank_partner_id.bank_ids. What the importer
        # puts there does not survive, and asserting it would be asserting
        # Odoo's compute rather than our matching.

    def test_an_unknown_counterparty_keeps_the_name_from_the_bank(self):
        lines = self._pull(statement_xml([movement(
            columns={2: "9999999999", 3: "0800", 10: "Někdo Nový"},
        )]))
        self.assertFalse(lines.partner_id)
        self.assertEqual(lines.partner_name, "Někdo Nový")
        self.assertEqual(lines.account_number, "99999999990800")

    def test_a_movement_with_no_counterparty_account(self):
        """Interest and fees carry no counter account at all."""
        lines = self._pull(statement_xml([movement(
            columns={8: "Připsaný úrok"}, amount="7.76",
        )]))
        self.assertFalse(lines.account_number)
        self.assertEqual(lines.payment_ref, "Připsaný úrok")

    # ------------------------------------------------------------------
    # official statements
    # ------------------------------------------------------------------

    def test_official_statement_carries_the_banks_balances(self):
        payload = statement_xml(
            [movement(movement_id=7, amount="-35.00")],
            info={
                "yearList": "2026", "idList": "4",
                "openingBalance": "7356.22", "closingBalance": "7321.22",
                "dateStart": None, "dateEnd": None,
            },
        )
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            side_effect=lambda _self, method, *a, **kw: (
                (2026, 4) if method == "last_statement" else payload
            ),
        ):
            lines = self.journal._fio_pull_official()
        statement = lines.statement_id
        self.assertEqual(len(statement), 1)
        self.assertEqual(statement.name, "4/2026")
        self.assertEqual(statement.balance_start, 7356.22)
        self.assertEqual(statement.balance_end_real, 7321.22)
        self.assertEqual(self.journal.fio_last_statement_number, 4)

    def test_official_mode_only_asks_for_what_is_missing(self):
        self.journal.sudo().write({
            "fio_last_statement_year": 2026, "fio_last_statement_number": 2,
        })
        self.assertEqual(
            self.journal._fio_statements_to_fetch(2026, 5, 12),
            [(2026, 3), (2026, 4), (2026, 5)],
        )

    def test_official_mode_restarts_the_count_in_a_new_year(self):
        """Fio numbers statements from 1 again every January."""
        self.journal.sudo().write({
            "fio_last_statement_year": 2025, "fio_last_statement_number": 12,
        })
        self.assertEqual(
            self.journal._fio_statements_to_fetch(2026, 2, 12),
            [(2026, 1), (2026, 2)],
        )

    def test_a_re_pulled_statement_lands_on_the_same_record(self):
        """The bank's statement 4/2026 is ONE document, however often it is read.

        A second pull that brings even one new movement must extend the
        existing ``account.bank.statement``, not create a namesake beside it —
        two records would split the document and break its balance check.
        """
        first = statement_xml(
            [movement(movement_id=1, amount="-10.00")],
            info={"yearList": "2026", "idList": "4",
                  "openingBalance": "100.00", "closingBalance": "90.00",
                  "dateStart": None, "dateEnd": None},
        )
        second = statement_xml(
            [movement(movement_id=1, amount="-10.00"),
             movement(movement_id=2, amount="-5.00")],
            info={"yearList": "2026", "idList": "4",
                  "openingBalance": "100.00", "closingBalance": "85.00",
                  "dateStart": None, "dateEnd": None},
        )
        vals = {"name": "4/2026"}
        self.journal._fio_add_balances(vals, self.journal._fio_parse(first).info)
        self.journal._fio_import_lines(self.journal._fio_parse(first).transactions, dict(vals))

        vals2 = {"name": "4/2026"}
        self.journal._fio_add_balances(vals2, self.journal._fio_parse(second).info)
        new_lines = self.journal._fio_import_lines(
            self.journal._fio_parse(second).transactions, dict(vals2),
        )

        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id), ("name", "=", "4/2026")]
        )
        self.assertEqual(len(statements), 1)
        self.assertEqual(len(statements.line_ids), 2)
        self.assertEqual(len(new_lines), 1)
        self.assertEqual(new_lines.fio_movement_id, "2")
        # The closing balance follows the newer read.
        self.assertEqual(statements.balance_end_real, 85.00)

    def test_a_statement_is_not_created_when_nothing_is_new(self):
        payload = statement_xml(
            [movement(movement_id=1)],
            info={"yearList": "2026", "idList": "5", "dateStart": None,
                  "dateEnd": None},
        )
        parsed = self.journal._fio_parse(payload)
        self.journal._fio_import_lines(parsed.transactions, {"name": "5/2026"})
        self.journal._fio_import_lines(parsed.transactions, {"name": "5/2026"})
        self.assertEqual(
            self.env["account.bank.statement"].search_count(
                [("journal_id", "=", self.journal.id), ("name", "=", "5/2026")]
            ),
            1,
        )

    def test_movements_mode_can_group_into_statements(self):
        self.journal.sudo().fio_create_statements = True
        lines = self._pull(statement_xml([movement(movement_id=8)]))
        self.assertTrue(lines.statement_id)
        self.assertIn(self.journal.code, lines.statement_id.name)

    def test_movements_mode_does_not_group_by_default(self):
        lines = self._pull(statement_xml([movement(movement_id=9)]))
        self.assertFalse(lines.statement_id)

    def test_bookmark_mode(self):
        self.journal.sudo().fio_pull_mode = "bookmark"
        lines = self._pull(statement_xml([movement(movement_id=11)]))
        self.assertEqual(lines.fio_movement_id, "11")

    def test_the_highest_movement_id_is_remembered(self):
        self._pull(statement_xml([
            movement(movement_id=5), movement(movement_id=77),
            movement(movement_id=40),
        ]))
        self.assertEqual(self.journal.fio_last_movement_id, "77")
        self.assertTrue(self.journal.fio_last_pull_at)

    def test_the_remembered_id_never_goes_backwards(self):
        self._pull(statement_xml([movement(movement_id=77)]))
        self._pull(statement_xml([movement(movement_id=5)]))
        self.assertEqual(self.journal.fio_last_movement_id, "77")

    def test_a_movement_in_the_wrong_currency_is_refused(self):
        """Fio reports a movement in its account's currency, so a mismatch is
        a journal configured for the wrong currency. Importing it used to book
        100 EUR as 100 CZK with only a log line to say so."""
        with self.assertRaises(UserError) as caught:
            self._pull(statement_xml([movement(currency="EUR")]))
        self.assertIn("EUR", str(caught.exception))
        self.assertFalse(self.env["account.bank.statement.line"].search_count([
            ("journal_id", "=", self.journal.id)]))

    def _foreign_currency(self, code="EUR"):
        currency = self.env["res.currency"].with_context(active_test=False).search(
            [("name", "=", code)], limit=1)
        currency.active = True
        return currency

    def test_a_card_payment_abroad_keeps_its_original_amount(self):
        eur = self._foreign_currency()
        lines = self._pull(statement_xml([movement(
            amount="-512.40", columns={18: "20.00 EUR"})]))
        self.assertEqual(lines.foreign_currency_id, eur)
        self.assertAlmostEqual(lines.amount_currency, -20.0)
        self.assertAlmostEqual(lines.amount, -512.40)

    def test_a_no_break_space_in_the_amount_is_read(self):
        self._foreign_currency()
        lines = self._pull(statement_xml([movement(
            amount="-30512.40", columns={18: "1\u00a0200.00 EUR"})]))
        self.assertAlmostEqual(lines.amount_currency, -1200.0)

    def test_an_unreadable_specification_is_left_alone(self):
        self._foreign_currency()
        lines = self._pull(statement_xml([movement(
            columns={18: "platba kartou 20 EUR Wien"})]))
        self.assertFalse(lines.foreign_currency_id)

    def test_a_specification_in_the_journal_currency_adds_nothing(self):
        lines = self._pull(statement_xml([movement(columns={18: "15.00 CZK"})]))
        self.assertFalse(lines.foreign_currency_id)

    def test_explanations_are_actionable(self):
        from odoo.addons.account_fio_base.utils.client import (
            FioHistoryLocked, FioRateLimited, FioTooMuchData,
        )

        self.assertIn("padlock", self.journal._fio_explain(FioHistoryLocked("x")))
        self.assertIn("shorter", self.journal._fio_explain(FioTooMuchData("x")))
        # Anything else is passed through rather than paraphrased away.
        self.assertEqual(self.journal._fio_explain(FioRateLimited("wait")), "wait")

    # ------------------------------------------------------------------
    # guard rails
    # ------------------------------------------------------------------

    def test_reaching_past_90_days_is_refused_until_confirmed(self):
        old = date.today() - timedelta(days=200)
        with self.assertRaises(UserError) as caught:
            self.journal._fio_check_history_window(old, confirmed=False)
        self.assertIn("padlock", str(caught.exception))
        # Confirmed, it goes through.
        self.journal._fio_check_history_window(old, confirmed=True)

    def test_recent_range_needs_no_confirmation(self):
        self.journal._fio_check_history_window(
            date.today() - timedelta(days=10), confirmed=False,
        )

    def test_a_long_range_is_chunked(self):
        chunks = self.journal._fio_chunks(date(2026, 1, 1), date(2026, 3, 31))
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0][0], date(2026, 1, 1))
        self.assertEqual(chunks[-1][1], date(2026, 3, 31))
        # No gaps, no overlaps.
        for (_start, end), (next_start, _next_end) in zip(chunks, chunks[1:]):
            self.assertEqual(next_start - end, timedelta(days=1))

    def test_one_broken_account_does_not_stop_the_cron(self):
        other_bank = self.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ5320100000002111111112",
            "partner_id": self.company.partner_id.id,
            "company_id": self.company.id,
        })
        self.env["account.journal"].sudo().create({
            "name": "Fio 2", "type": "bank", "code": "FIOB2",
            "company_id": self.company.id,
            "bank_account_id": other_bank.id,
            "fio_token_read": "b" * 64,
            "bank_statements_source": "fio",
        })
        calls = []

        def fail_first(_self, *args, **kwargs):
            calls.append(_self.id)
            if len(calls) == 1:
                raise ValueError("boom")
            return statement_xml([movement(movement_id=99)])

        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          side_effect=fail_first):
            self.env["account.journal"]._fio_cron_pull_statements()
        self.assertEqual(len(calls), 2)
        # The one that worked kept its line: the failing account's rollback
        # must not reach past its own savepoint.
        self.assertEqual(
            self.env["account.bank.statement.line"].search_count([
                ("fio_movement_id", "=", "99"),
            ]), 1,
        )

    def test_the_cron_keeps_the_lines_it_imported(self):
        """The success path must RELEASE the savepoint, not roll it back.

        ``Savepoint.close()`` is ``close(self, *, rollback=True)``, so the bare
        ``savepoint.close()`` that read like "release this" threw away every
        line the pull had just created — at the exact moment it succeeded. The
        account's own stamps were still unflushed in the ORM cache and survived
        the rollback, so the run left ``last_read_at``, ``last_pull_at`` and the
        correct ``last_movement_id`` behind and no lines: successful-looking in
        every field an operator checks. Diagnosed on the 18.0 twin against a
        real Fio account, where the interactive pull imported 15 lines and the
        cron imported none.

        The assertion is a ``search``, not the returned recordset — the whole
        point is whether the rows are still in the database afterwards.
        """
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            return_value=statement_xml([movement(movement_id=4242)]),
        ):
            self.env["account.journal"]._fio_cron_pull_statements()
        lines = self.env["account.bank.statement.line"].search([
            ("journal_id", "=", self.journal.id),
        ])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.fio_movement_id, "4242")

    def test_a_failed_pull_does_not_leave_its_bookmark_behind(self):
        """The rollback has to clear the ORM cache, not just the SQL.

        ``cr.savepoint(flush=False)`` returns the plain ``Savepoint``, whose
        ``rollback()`` does not ``cr.clear()``. Writes the pull had made were
        still sitting unflushed when the rollback ran, so they survived it and
        were written afterwards — recording a bookmark for movements that had
        just been discarded. The next run would then skip them for good.
        """
        def write_then_fail(_self, *args, **kwargs):
            _self.sudo().fio_last_movement_id = "999999"
            raise ValueError("boom, after the bookmark was written")

        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          side_effect=write_then_fail):
            self.env["account.journal"]._fio_cron_pull_statements()
        self.assertNotEqual(self.journal.fio_last_movement_id, "999999")

    def test_a_quiet_account_still_records_that_it_was_pulled(self):
        """``last_pull_at`` used to be written inside ``_fio_import_lines``,
        which returns early when there is nothing new. An account that had
        simply been quiet therefore showed a last pull weeks in the past —
        indistinguishable from a feed that had stopped, which is the one
        question the field exists to answer."""
        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          return_value=statement_xml([])):
            self.env["account.journal"]._fio_cron_pull_statements()
        self.assertTrue(self.journal.fio_last_pull_at)


    # ------------------------------------------------------------------
    # configuration
    # ------------------------------------------------------------------

    def test_the_cron_only_visits_journals_whose_feed_is_fio(self):
        """Every journal now carries the Fio fields, so the cron's domain is the
        only thing separating a Fio journal from the sales journal. A plain bank
        journal, and a journal that has a Fio token but is fed some other way,
        must both be left alone."""
        self.env["account.journal"].sudo().create({
            "name": "Plain bank", "type": "bank", "code": "PLNBK",
            "company_id": self.company.id,
        })
        self.env["account.journal"].sudo().create({
            "name": "Fio payments only", "type": "bank", "code": "FIOPO",
            "company_id": self.company.id,
            # A token, but the statements arrive some other way.
            "fio_token_write": "f" * 64,
        })
        visited = []

        def record(_self, *args, **kwargs):
            visited.append(_self.id)
            return statement_xml([movement(movement_id=123)])

        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          side_effect=record):
            self.env["account.journal"]._fio_cron_pull_statements()
        self.assertEqual(visited, [self.journal.id])

    def test_a_cron_failure_does_not_publish_the_token_to_the_chatter(self):
        """The handler catches ``Exception``, not just ``FioError``, so it can
        be handed a message the client never sanitised — and Fio carries the
        token in the URL path. Everyone following the journal reads that
        chatter."""
        token = "a" * 64
        leaky = "HTTPSConnectionPool: /ib_api/rest/periods/%s/2026-01-01/" % token

        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          side_effect=RuntimeError(leaky)):
            self.env["account.journal"]._fio_cron_pull_statements()
        body = self.journal.message_ids[0].body
        self.assertNotIn(token, body)
        self.assertIn("***", body)

    def test_fio_is_offered_as_a_bank_feed_without_hiding_the_others(self):
        """The extension point is name-mangled: because
        ``__get_bank_statements_available_sources`` starts with two
        underscores, every reference to it compiles to
        ``_<ClassName>__get_...``. An override written in a class named
        anything but ``AccountJournal`` therefore does not override core's at
        all — and the failure is silent, because the field simply offers a
        different set of sources. Assert both halves: Fio is there, and so is
        what was there before."""
        sources = dict(
            self.env["account.journal"]
            ._fields["bank_statements_source"]
            ._description_selection(self.env)
        )
        self.assertIn("fio", sources)
        self.assertIn("undefined", sources)

    def test_a_journal_fed_by_fio_must_have_a_read_token(self):
        """Refused at save time rather than an hour later in the cron, where it
        would post the same failure to the chatter every hour."""
        from odoo.exceptions import ValidationError

        journal = self.env["account.journal"].sudo().create({
            "name": "Fio tokenless", "type": "bank", "code": "FIOTL",
            "company_id": self.company.id,
        })
        with self.assertRaises(ValidationError) as caught:
            journal.bank_statements_source = "fio"
        self.assertIn("no Fio read token", str(caught.exception))

    def test_a_truncated_token_is_refused(self):
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self.env["account.journal"].sudo().create({
                "name": "Fio 3", "type": "bank", "code": "FIOB3",
                "company_id": self.company.id,
                "fio_token_read": "too-short",
            })


@tagged("post_install", "-at_install")
class TestFioPullWizard(FioCommon):
    def _wizard(self, **vals):
        return self.env["fio.statement.pull"].create(
            dict({"journal_id": self.journal.id}, **vals)
        )

    def test_the_call_count_is_shown_before_the_run(self):
        """One call per 30 seconds — a year is a six-minute operation, and the
        user should learn that before starting it, not during."""
        wizard = self._wizard(
            mode="movements", date_from=date(2026, 1, 1), date_to=date(2026, 3, 31),
        )
        self.assertEqual(wizard.call_count, 3)

    def test_the_call_count_for_official_statements(self):
        wizard = self._wizard(
            mode="official", statement_year=2026, statement_from=1, statement_to=4,
        )
        self.assertEqual(wizard.call_count, 4)

    def test_the_unlock_warning_appears_only_when_it_is_needed(self):
        recent = self._wizard(date_from=date.today() - timedelta(days=10))
        self.assertFalse(recent.needs_history_unlock)
        old = self._wizard(date_from=date.today() - timedelta(days=200))
        self.assertTrue(old.needs_history_unlock)

    def test_an_old_range_is_refused_without_the_confirmation(self):
        wizard = self._wizard(
            date_from=date.today() - timedelta(days=200), date_to=date.today(),
        )
        with self.assertRaises(UserError):
            wizard.action_pull()

    def test_reversed_dates_are_refused(self):
        wizard = self._wizard(
            date_from=date(2026, 3, 1), date_to=date(2026, 1, 1),
        )
        with self.assertRaises(UserError):
            wizard.action_pull()

    def test_reversed_statement_numbers_are_refused(self):
        wizard = self._wizard(mode="official", statement_from=5, statement_to=2)
        with self.assertRaises(UserError):
            wizard.action_pull()

    def test_pulling_a_range_of_official_statements(self):
        payload = statement_xml(
            [movement(movement_id=31)],
            info={"yearList": "2026", "idList": "1", "dateStart": None,
                  "dateEnd": None},
        )
        wizard = self._wizard(
            mode="official", statement_year=2026, statement_from=1, statement_to=1,
        )
        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          return_value=payload):
            action = wizard.action_pull()
        self.assertEqual(action["res_model"], "account.bank.statement.line")

    def test_a_pull_that_finds_nothing_says_so(self):
        wizard = self._wizard(
            date_from=date.today() - timedelta(days=1), date_to=date.today(),
        )
        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          return_value=statement_xml([])):
            action = wizard.action_pull()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "warning")

    def test_a_bank_refusal_is_translated_before_it_reaches_the_user(self):
        from odoo.addons.account_fio_base.utils.client import FioHistoryLocked

        wizard = self._wizard(
            date_from=date.today() - timedelta(days=10), date_to=date.today(),
        )
        with patch.object(type(self.journal), "_fio_call", autospec=True,
                          side_effect=FioHistoryLocked("422")), \
                self.assertRaises(UserError) as caught:
            wizard.action_pull()
        self.assertIn("padlock", str(caught.exception))
