# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_gpc_base.tests.gpc_fixtures import (
    ACCOUNT,
    gpc_file as _gpc_file,
    rec074 as _rec074,
    rec075 as _rec075,
)


@tagged("post_install", "-at_install")
class TestStatementImportGpc(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.bank_account = cls.env["res.partner.bank"].create({
            "acc_number": ACCOUNT,
            "partner_id": cls.env.company.partner_id.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "GPC Bank",
            "code": "GPCBK",
            "type": "bank",
            "bank_account_id": cls.bank_account.id,
            "currency_id": cls.czk.id,
        })

    def _import(self, file_b64, filename="vypis.gpc"):
        wizard = self.env["account.statement.import"].with_context(
            journal_id=self.journal.id
        ).create({
            "statement_file": file_b64,
            "statement_filename": filename,
        })
        return wizard.import_file_button()

    def test_import_statement(self):
        self._import(_gpc_file(
            _rec074(),
            _rec075(),
            _rec075(
                doc_number="1234568",
                amount=100000,
                code="1",
                vs="555",
                ks="",
                bank_code="",
                ss="77",
                client="DODAVATEL SRO",
                counter_account="2600123456",
            ),
        ))
        statement = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(statement), 1)
        self.assertEqual(statement.name, "GPC %s/7" % ACCOUNT)
        self.assertAlmostEqual(statement.balance_start, 10000.0)
        self.assertAlmostEqual(statement.balance_end_real, 11234.5)
        lines = statement.line_ids.sorted("amount")
        self.assertEqual(len(lines), 2)
        credit = lines[-1]
        self.assertAlmostEqual(credit.amount, 1234.5)
        self.assertIn("VS:20260042", credit.payment_ref)
        self.assertIn("KS:0308", credit.payment_ref)
        self.assertIn("19012333/0300", credit.payment_ref)
        self.assertEqual(credit.partner_name, "ODBERATEL AS")
        debit = lines[0]
        self.assertAlmostEqual(debit.amount, -1000.0)
        self.assertIn("VS:555", debit.payment_ref)
        self.assertIn("SS:77", debit.payment_ref)
        self.assertNotIn("KS:", debit.payment_ref)

    def test_symbol_fields_when_available(self):
        self._import(_gpc_file(_rec074(), _rec075()))
        line = self.env["account.bank.statement.line"].search(
            [("journal_id", "=", self.journal.id)]
        )
        if "variable_symbol" in line._fields:
            self.assertEqual(line.variable_symbol, "20260042")
            self.assertEqual(line.constant_symbol, "0308")

    def test_reimport_dedup(self):
        from odoo.exceptions import UserError
        gpc = _gpc_file(_rec074(), _rec075())
        self._import(gpc)
        # a file with only already-imported transactions is refused ...
        with self.assertRaises(UserError):
            self._import(gpc, filename="vypis2.gpc")
        # ... and a file with one known + one new line imports only the new
        self._import(
            _gpc_file(
                _rec074(),
                _rec075(),
                _rec075(doc_number="1234570", amount=5000, code="2"),
            ),
            filename="vypis3.gpc",
        )
        lines = self.env["account.bank.statement.line"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(lines), 2)

    def test_storno_codes(self):
        self._import(_gpc_file(
            _rec074(),
            _rec075(code="4", doc_number="900001"),
            _rec075(code="5", doc_number="900002"),
        ))
        lines = self.env["account.bank.statement.line"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(
            sorted(lines.mapped("amount")), [-1234.5, 1234.5]
        )

    def test_non_gpc_falls_through(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self._import(
                base64.b64encode(b"definitely,not,gpc\n1,2,3\n"),
                filename="whatever.csv",
            )

    def test_multi_statement_file(self):
        self._import(_gpc_file(
            _rec074(number="007"),
            _rec075(),
            _rec074(
                number="008",
                old_balance=1123450,
                new_balance=1023450,
                date="020726",
            ),
            _rec075(
                code="1",
                amount=100000,
                doc_number="1234569",
                date="020726",
            ),
        ))
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)], order="date"
        )
        self.assertEqual(len(statements), 2)
        self.assertEqual(len(statements.mapped("line_ids")), 2)
