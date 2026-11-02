# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from decimal import Decimal
# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from odoo.addons.account_fio_base.utils.statement import (
    FioParseError,
    parse_fio_json,
    parse_fio_xml,
    parse_movements,
)

from .fio_fixtures import movement, statement_json, statement_xml


class TestFioStatementParser(TestCase):
    """Both movement formats, and the traps that make them lie."""

    def test_xml_info(self):
        stmt = parse_fio_xml(statement_xml())
        self.assertEqual(stmt.info.account_id, "2111111111")
        self.assertEqual(stmt.info.iban, "CZ8020100000002111111111")
        self.assertEqual(stmt.info.opening_balance, Decimal("7356.22"))
        self.assertEqual(stmt.info.closing_balance, Decimal("7321.22"))
        self.assertEqual(stmt.info.date_start, date(2012, 7, 1))
        self.assertEqual(stmt.transactions, [])

    def test_xml_columns(self):
        stmt = parse_fio_xml(statement_xml([movement(columns={
            2: "2222233333", 3: "2010", 4: "0558", 5: "1234567890",
            6: "9876543210", 10: "Béďa Trávníček", 12: "Fio banka, a.s.",
            16: "Za zboží", 17: 2102392862, 25: "Můj test",
            26: "UNCRITMMXXX", 27: "2000000003", 8: "Platba převodem",
        })]))
        tx = stmt.transactions[0]
        self.assertEqual(tx["movement_id"], 1147608196)
        self.assertEqual(tx["date"], date(2012, 7, 27))
        self.assertEqual(tx["amount"], Decimal("-15.00"))
        self.assertEqual(tx["counter_account"], "2222233333")
        self.assertEqual(tx["counter_bank_code"], "2010")
        self.assertEqual(tx["ks"], "0558")
        self.assertEqual(tx["vs"], "1234567890")
        self.assertEqual(tx["ss"], "9876543210")
        self.assertEqual(tx["counter_account_name"], "Béďa Trávníček")
        self.assertEqual(tx["message_for_recipient"], "Za zboží")
        self.assertEqual(tx["instruction_id"], 2102392862)
        self.assertEqual(tx["comment"], "Můj test")
        self.assertEqual(tx["counter_bic"], "UNCRITMMXXX")
        self.assertEqual(tx["payer_reference"], "2000000003")

    def test_date_offset_is_not_a_timezone(self):
        """A ``+02:00`` date must not be shifted back a day by a UTC round trip."""
        stmt = parse_fio_xml(statement_xml([
            movement(date="2012-07-27+02:00"),
            movement(movement_id=2, date="2012-01-15+01:00"),
        ]))
        self.assertEqual(stmt.transactions[0]["date"], date(2012, 7, 27))
        self.assertEqual(stmt.transactions[1]["date"], date(2012, 1, 15))

    def test_json_epoch_dates(self):
        """The documented example returns milliseconds, not the documented string."""
        stmt = parse_fio_json(statement_json([
            movement(date=1340661600000, amount=1.00),
        ]))
        self.assertEqual(stmt.transactions[0]["date"], date(2012, 6, 26))
        self.assertEqual(stmt.info.date_start, date(2012, 6, 26))

    def test_json_string_dates(self):
        stmt = parse_fio_json(statement_json(
            [movement(date="2012-06-26+02:00", amount=1.00)], epoch_dates=False,
        ))
        self.assertEqual(stmt.transactions[0]["date"], date(2012, 6, 26))

    def test_json_null_columns_are_skipped(self):
        stmt = parse_fio_json(statement_json([movement(columns={5: None, 10: None})]))
        self.assertNotIn("vs", stmt.transactions[0])
        self.assertNotIn("counter_account_name", stmt.transactions[0])

    def test_blank_column_is_dropped(self):
        """Fio pads empty text columns with a single space."""
        stmt = parse_fio_xml(statement_xml([movement(columns={7: " "})]))
        self.assertNotIn("user_identification", stmt.transactions[0])

    def test_amount_precision(self):
        stmt = parse_fio_xml(statement_xml([movement(amount="-12225.25")]))
        self.assertEqual(stmt.transactions[0]["amount"], Decimal("-12225.25"))

    def test_reversal_shares_the_instruction_id(self):
        """§5.3: a storno has a NEW movement id and the ORIGINAL instruction id.

        Nothing in the parser may collapse the two — that would silently drop
        the reversal and leave the balance wrong.
        """
        stmt = parse_fio_xml(statement_xml([
            movement(movement_id=1, amount="100.00", columns={17: 555}),
            movement(movement_id=2, amount="-100.00", columns={17: 555}),
        ]))
        self.assertEqual(len(stmt.transactions), 2)
        self.assertEqual(
            {tx["instruction_id"] for tx in stmt.transactions}, {555},
        )
        self.assertEqual(
            [tx["movement_id"] for tx in stmt.transactions], [1, 2],
        )

    def test_empty_transaction_list(self):
        stmt = parse_fio_json(statement_json([]))
        self.assertEqual(stmt.transactions, [])
        self.assertEqual(stmt.info.account_id, "2111111111")

    def test_official_statement_info(self):
        stmt = parse_fio_xml(statement_xml(info={
            "yearList": "2012", "idList": "4",
            "dateStart": None, "dateEnd": None,
        }))
        self.assertEqual(stmt.info.year_list, 2012)
        self.assertEqual(stmt.info.id_list, 4)

    def test_rejects_foreign_xml(self):
        with self.assertRaises(FioParseError):
            parse_fio_xml(b"<html><body>nope</body></html>")

    def test_rejects_garbage(self):
        with self.assertRaises(FioParseError):
            parse_fio_json(b"not json")

    def test_xxe_is_not_resolved(self):
        payload = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            b"<AccountStatement><Info><accountId>&x;</accountId></Info>"
            b"</AccountStatement>"
        )
        try:
            stmt = parse_fio_xml(payload)
        except FioParseError:
            return  # refusing the document outright is also fine
        self.assertNotIn("root:", stmt.info.account_id or "")

    def test_info_with_everything_null(self):
        """The header-only answer Fio returns for a period with no movements."""
        stmt = parse_fio_json(statement_json([], info={
            "openingBalance": None, "closingBalance": None,
            "dateStart": None, "dateEnd": None,
        }))
        self.assertIsNone(stmt.info.opening_balance)
        self.assertIsNone(stmt.info.date_start)
        self.assertEqual(stmt.info.account_id, "2111111111")
        self.assertEqual(stmt.transactions, [])

    def test_json_with_a_null_transaction_list(self):
        """Fio sends ``transactionList: null``, not an empty list."""
        stmt = parse_fio_json(
            b'{"accountStatement":{"info":{"accountId":"1"},'
            b'"transactionList":null}}'
        )
        self.assertEqual(stmt.transactions, [])

    def test_xml_without_a_transaction_list_element(self):
        payload = (
            b"<AccountStatement><Info><accountId>1</accountId></Info>"
            b"</AccountStatement>"
        )
        self.assertEqual(parse_fio_xml(payload).transactions, [])

    def test_an_unknown_column_is_ignored_not_fatal(self):
        """Fio has added columns before; a new one must not break the import."""
        stmt = parse_fio_xml(statement_xml([movement(columns={99: "future"})]))
        self.assertEqual(len(stmt.transactions), 1)
        self.assertNotIn("future", str(stmt.transactions[0]))

    def test_a_positive_and_a_negative_amount(self):
        stmt = parse_fio_xml(statement_xml([
            movement(movement_id=1, amount="1234.56"),
            movement(movement_id=2, amount="-1234.56"),
        ]))
        self.assertEqual(
            [tx["amount"] for tx in stmt.transactions],
            [Decimal("1234.56"), Decimal("-1234.56")],
        )

    def test_a_bad_amount_is_reported_not_silently_zeroed(self):
        with self.assertRaises(FioParseError):
            parse_fio_xml(statement_xml([movement(amount="not a number")]))

    def test_a_bad_date_is_reported(self):
        with self.assertRaises(FioParseError):
            parse_fio_xml(statement_xml([movement(date="27. 7. 2012")]))

    def test_dispatch(self):
        self.assertEqual(
            parse_movements(statement_xml(), "xml").info.bank_id, "2010",
        )
        self.assertEqual(
            parse_movements(statement_json(), "json").info.bank_id, "2010",
        )
        with self.assertRaises(ValueError):
            parse_movements(b"", "gpc")
