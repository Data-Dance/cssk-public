# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_mt940_base.tests import mt940_fixtures as f


@tagged("post_install", "-at_install")
class TestStatementImportMt940(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        # stored as the IBAN, while ČS writes :25: as 0800/192000145399
        cls.bank_account = cls.env["res.partner.bank"].create({
            "acc_number": f.CS_IBAN,
            "partner_id": cls.env.company.partner_id.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "MT940 Bank",
            "code": "M940",
            "type": "bank",
            "bank_account_id": cls.bank_account.id,
            "currency_id": cls.czk.id,
        })
        cls.customer = cls.env["res.partner"].create({"name": "Odběratel a.s."})
        cls.env["res.partner.bank"].create({
            "acc_number": "19012333/0300",
            "partner_id": cls.customer.id,
        })

    def _import(self, file_b64, filename="vypis.sta", journal=None):
        wizard = self.env["account.statement.import"].with_context(
            journal_id=(journal or self.journal).id
        ).create({
            "statement_file": file_b64,
            "statement_filename": filename,
        })
        return wizard.import_file_button()

    def _statement_file(self, *transactions, **kwargs):
        return f.mt940_file(f.cs_message(list(transactions), **kwargs))

    def _lines(self, journal=None):
        return self.env["account.bank.statement.line"].search(
            [("journal_id", "=", (journal or self.journal).id)]
        )

    def test_import_statement(self):
        self._import(self._statement_file(
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86()),
        ))
        statement = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(statement), 1)
        self.assertEqual(statement.name, "MT940 %s/24" % f.CS_ACCOUNT)
        self.assertAlmostEqual(statement.balance_start, 10000.0)
        self.assertAlmostEqual(statement.balance_end_real, 11234.5)
        line = statement.line_ids
        self.assertAlmostEqual(line.amount, 1234.5)
        self.assertIn("VS:20260042", line.payment_ref)
        self.assertEqual(line.partner_name, "ODBERATEL AS")
        # found through the counterparty account in ?30/?31
        self.assertEqual(line.partner_id, self.customer)
        self.assertEqual(line.transaction_type, "NMSC")
        self.assertIn(":86:", line.raw_data)
        self.assertEqual(line.ref, "0000123456")

    def test_journal_found_from_national_form(self):
        """The statement says 0800/192000145399, the journal holds the IBAN:
        the framework's own ilike on the sanitized number cannot pair them."""
        other = self.env["account.journal"].create({
            "name": "Other Bank", "code": "OTHB", "type": "bank",
            "currency_id": self.czk.id,
        })
        # started from the wrong journal, the matched one is named
        with self.assertRaisesRegex(UserError, "MT940 Bank"):
            self._import(self._statement_file(
                ("2607010701C1234,50NMSCNONREF", f.cs_domestic_86()),
            ), journal=other)

    def test_journal_stored_in_national_form(self):
        self.bank_account.acc_number = f.CS_ACCOUNT
        self._import(self._statement_file(
            ("2607010701C1234,50NMSCNONREF", f.cs_domestic_86()),
        ))
        self.assertEqual(len(self._lines()), 1)

    def test_symbol_fields_when_available(self):
        self._import(self._statement_file(
            ("2607010701C1234,50NMSCNONREF", f.cs_domestic_86()),
        ))
        line = self._lines()
        if "variable_symbol" not in line._fields:
            self.skipTest("no module provides the symbol fields")
        self.assertEqual(line.variable_symbol, "20260042")
        self.assertEqual(line.constant_symbol, "0308")
        self.assertEqual(line.specific_symbol, "77")

    def test_reimport_dedup(self):
        first = self._statement_file(
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86()),
        )
        self._import(first)
        with self.assertRaises(UserError):
            self._import(first, filename="vypis2.sta")
        # one known + one new line: only the new one is imported
        self._import(self._statement_file(
            ("2607010701C1234,50NMSC0000123456//1234567890",
             f.cs_domestic_86()),
            ("2607010701D34,50NMSCNONREF//1234567899", "POPLATEK"),
            closing="C260701CZK11200,00",
        ), filename="vypis3.sta")
        self.assertEqual(len(self._lines()), 2)

    def test_non_mt940_falls_through(self):
        with self.assertRaises(UserError):
            self._import(base64.b64encode(b"definitely,not,mt940\n1,2,3\n"),
                         filename="whatever.csv")

    def test_multi_account_file(self):
        rb_bank = self.env["res.partner.bank"].create({
            "acc_number": "CZ3855000000000112233088",
            "partner_id": self.env.company.partner_id.id,
        })
        rb_journal = self.env["account.journal"].create({
            "name": "RB", "code": "RBBK", "type": "bank",
            "bank_account_id": rb_bank.id, "currency_id": self.czk.id,
        })
        data = f.mt940_file(
            f.cs_message([("2607010701C1234,50NMSCNONREF", f.cs_domestic_86())]),
            f.rb_message([
                ("260701D113,37NMSC3598473723//O-GE-CC", f.rb_domestic_86()),
                ("260701C300,00NMSC3598473724//GPP-SEPA", f.rb_sepa_86()),
            ]),
        )
        wizard = self.env["account.statement.import"].create({
            "statement_file": data, "statement_filename": "multi.sta",
        })
        wizard.import_file_button()
        self.assertEqual(len(self._lines()), 1)
        rb_lines = self._lines(rb_journal)
        self.assertEqual(len(rb_lines), 2)
        self.assertAlmostEqual(sum(rb_lines.mapped("amount")), 186.63)
