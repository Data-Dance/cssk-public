# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Parser semantics, without the import framework."""

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_mt940_base.utils.mt940 import (
    is_mt940,
    parse_86,
    parse_mt940,
    statement_account,
)

from . import mt940_fixtures as f


@tagged("post_install", "-at_install")
class TestMt940Parser(TransactionCase):
    def _single(self, data, **kwargs):
        triplets = parse_mt940(data, **kwargs)
        self.assertEqual(len(triplets), 1)
        return triplets[0]

    def test_statement_account_forms(self):
        # ČS: bank code, then prefix and 10-digit number run together
        self.assertEqual(statement_account("0800/192000145399"),
                         "19-2000145399/0800")
        self.assertEqual(statement_account("0800/9944040012345671"),
                         "994404-12345671/0800")
        # RB: bank code and the zero-padded 10-digit number, no prefix
        self.assertEqual(statement_account("5500/0112233088"), "112233088/5500")
        # IBAN, bare or behind a BIC
        self.assertEqual(statement_account("GIBACZPX/CZ6508000000192000145399"),
                         "CZ6508000000192000145399")

    def test_cs_domestic_symbols_and_counterparty(self):
        currency, account, stmts = self._single(f.mt940_bytes(f.cs_message([
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86()),
        ])), with_symbols=True)
        self.assertEqual((currency, account), ("CZK", f.CS_ACCOUNT))
        stmt = stmts[0]
        self.assertEqual(stmt["name"], "MT940 %s/24" % f.CS_ACCOUNT)
        self.assertAlmostEqual(stmt["balance_start"], 10000.0)
        self.assertAlmostEqual(stmt["balance_end_real"], 11234.5)
        line = stmt["transactions"][0]
        self.assertAlmostEqual(line["amount"], 1234.5)
        self.assertEqual(line["variable_symbol"], "20260042")
        # KS is the 4-digit code, as GPC carries it
        self.assertEqual(line["constant_symbol"], "0308")
        self.assertEqual(line["specific_symbol"], "77")
        self.assertEqual(line["account_number"], "19012333/0300")
        self.assertEqual(line["partner_name"], "ODBERATEL AS")
        self.assertEqual(line["transaction_type"], "NMSC")
        self.assertIn("FAKTURA 2026/0042", line["payment_ref"])
        self.assertIn("VS:20260042", line["payment_ref"])
        # the counterparty-symbol placeholder is not remittance text
        self.assertNotIn("VS2", line["payment_ref"])

    def test_symbols_only_on_request(self):
        _c, _a, stmts = self._single(f.mt940_bytes(f.cs_message([
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86()),
        ])))
        line = stmts[0]["transactions"][0]
        self.assertNotIn("variable_symbol", line)
        # … but the label still carries them, for matching without the module
        self.assertIn("VS:20260042", line["payment_ref"])

    def test_rb_dialect(self):
        _c, account, stmts = self._single(f.mt940_bytes(f.rb_message([
            ("260701D113,37NMSC3598473723//O-GE-CC", f.rb_domestic_86()),
            ("260701C300,00NMSC3598473724//GPP-SEPA", f.rb_sepa_86()),
        ]), header=()), with_symbols=True)
        self.assertEqual(account, f.RB_ACCOUNT)
        domestic, sepa = stmts[0]["transactions"]
        # RB puts KS in ?21 and VS in ?22 — recognised by prefix, not number
        self.assertEqual(domestic["variable_symbol"], "45135784")
        self.assertEqual(domestic["constant_symbol"], "0308")
        self.assertEqual(domestic["specific_symbol"], "1234578")
        self.assertEqual(domestic["account_number"], "19-32103210/6800")
        # a full 27-character ?32 continues in ?33
        self.assertEqual(domestic["partner_name"],
                         "STAVEBNI FIRMA NOVAK A SYNOVE S.R.O.")
        self.assertNotIn("BANKOVNI VYPIS", domestic["payment_ref"])
        self.assertNotIn("POPL.TRN", domestic["payment_ref"])
        self.assertAlmostEqual(domestic["amount"], -113.37)
        # ?38 IBAN wins over the ?30/?31 pair
        self.assertEqual(sepa["account_number"], "DE89370400440532013000")
        self.assertEqual(sepa["partner_name"], "FOREIGN GMBH")
        self.assertIn("INVOICE 77", sepa["payment_ref"])

    def test_reversal_marks(self):
        _c, _a, stmts = self._single(f.mt940_bytes(f.cs_message([
            ("2607010701RC10,00NMSCNONREF", "STORNO KREDITU"),
            ("2607010701RD4,50NMSCNONREF", "STORNO DEBETU"),
        ], closing="C260701CZK9994,50")))
        amounts = [t["amount"] for t in stmts[0]["transactions"]]
        # RC takes back a credit (money out), RD a debit (money in)
        self.assertEqual(amounts, [-10.0, 4.5])

    def test_entry_date_across_year_boundary(self):
        _c, _a, stmts = self._single(f.mt940_bytes(f.cs_message([
            # value 2 Jan 2027, booked 31 Dec: the booking year is 2026
            ("2701021231C5,00NMSCNONREF", "UROK"),
            ("261231C1,00NMSCNONREF", "BEZ DATA ZAUCTOVANI"),
        ], opening="C261231CZK0,00", closing="C261231CZK6,00")))
        dates = [t["date"] for t in stmts[0]["transactions"]]
        self.assertEqual(dates, [date(2026, 12, 31), date(2026, 12, 31)])

    def test_free_text_86(self):
        _c, _a, stmts = self._single(f.mt940_bytes(f.cs_message([
            ("2607010701D10,00NMSCNONREF", "POPLATEK ZA VEDENI VS:42"),
        ], closing="C260701CZK9990,00")), with_symbols=True)
        line = stmts[0]["transactions"][0]
        self.assertEqual(line["variable_symbol"], "42")
        # said once, not appended again
        self.assertEqual(line["payment_ref"].count("VS:42"), 1)

    def test_continued_statement_is_one(self):
        """Page 2 of the same :28: number opens with the intermediate 60M."""
        data = f.mt940_bytes(
            f.cs_message([("2607010701C1,00NMSCNONREF", "A")],
                         number="00024/00001", closing="C260701CZK10001,00",
                         closing_tag="62M"),
            f.cs_message([("2607010701C2,00NMSCNONREF", "B")],
                         number="00024/00002", opening="C260701CZK10001,00",
                         opening_tag="60M", closing="C260701CZK10003,00"),
        )
        _c, _a, stmts = self._single(data)
        self.assertEqual(len(stmts), 1)
        self.assertEqual(len(stmts[0]["transactions"]), 2)
        self.assertAlmostEqual(stmts[0]["balance_start"], 10000.0)
        self.assertAlmostEqual(stmts[0]["balance_end_real"], 10003.0)
        ids = {t["unique_import_id"] for t in stmts[0]["transactions"]}
        self.assertEqual(len(ids), 2)

    def test_continuation_must_meet_the_previous_balance(self):
        """Same :28: number, but the 60M does not pick up where page 1
        closed: not a continuation, so kept apart rather than merged."""
        data = f.mt940_bytes(
            f.cs_message([("2607010701C1,00NMSCNONREF", "A")],
                         number="00024/00001", closing="C260701CZK10001,00",
                         closing_tag="62M"),
            f.cs_message([("2607010701C2,00NMSCNONREF", "B")],
                         number="00024/00002", opening="C260701CZK500,00",
                         opening_tag="60M", closing="C260701CZK502,00"),
        )
        _c, _a, stmts = self._single(data)
        self.assertEqual(len(stmts), 2)

    def test_supplementary_details_in_label(self):
        data = f.mt940_bytes(f.cs_message([
            ("2607010701C1,00NMSCNONREF\r\nPUVODNI CASTKA EUR 0,04", "PREVOD"),
        ], closing="C260701CZK10001,00"))
        _c, _a, stmts = self._single(data)
        line = stmts[0]["transactions"][0]
        self.assertIn("PUVODNI CASTKA EUR 0,04", line["payment_ref"])
        self.assertAlmostEqual(line["amount"], 1.0)

    def test_two_accounts_two_triplets(self):
        data = f.mt940_bytes(
            f.cs_message([("2607010701C1,00NMSCNONREF", "A")],
                         closing="C260701CZK10001,00"),
            f.rb_message([("260701C1,00NMSCX//Y", "B")],
                         closing="C260701CZK22244462,04"),
        )
        accounts = [account for _c, account, _s in parse_mt940(data)]
        self.assertEqual(accounts, [f.CS_ACCOUNT, f.RB_ACCOUNT])

    def test_identical_lines_get_distinct_ids(self):
        _c, _a, stmts = self._single(f.mt940_bytes(f.cs_message([
            ("2607010701D5,00NMSCNONREF", "POPLATEK"),
            ("2607010701D5,00NMSCNONREF", "POPLATEK"),
        ], closing="C260701CZK9990,00")))
        ids = [t["unique_import_id"] for t in stmts[0]["transactions"]]
        self.assertEqual(len(set(ids)), 2)

    def test_encodings(self):
        name = "ODBĚRATEL ŽLUŤOUČKÝ AS"
        message = f.cs_message([
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86(name=name)),
        ])
        for encoding in ("cp852", "cp1250", "utf-8"):
            with self.subTest(encoding=encoding):
                _c, _a, stmts = self._single(
                    f.mt940_bytes(message, encoding=encoding))
                self.assertEqual(stmts[0]["transactions"][0]["partner_name"],
                                 name)

    def test_parse_86_raw_values(self):
        code, subfields = parse_86(["020?20KS:308?21VS:1", "23?32NAME"])
        self.assertEqual(code, "020")
        # a value split across lines is rejoined
        self.assertEqual(subfields["21"], "VS:123")
        self.assertIsNone(parse_86(["just free text"]))

    def test_not_mt940(self):
        self.assertEqual(parse_mt940(b"definitely,not,mt940\n1,2,3\n"), [])
        self.assertFalse(is_mt940(b"074000000192000145399"))
        self.assertTrue(is_mt940(f.mt940_bytes(f.cs_message([]))))

    def test_statement_without_lines_is_dropped(self):
        self.assertEqual(parse_mt940(f.mt940_bytes(f.cs_message(
            [], closing="C260701CZK10000,00"))), [])
