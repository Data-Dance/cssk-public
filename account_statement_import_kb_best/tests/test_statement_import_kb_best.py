# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_kb_best_base.tests import best_fixtures as f


@tagged("post_install", "-at_install")
class TestStatementImportKbBest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        # the national form; the statement names the account by IBAN
        cls.bank_account = cls.env["res.partner.bank"].create({
            "acc_number": f.NATIONAL,
            "partner_id": cls.env.company.partner_id.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "KB", "code": "KBST", "type": "bank",
            "bank_account_id": cls.bank_account.id,
            "currency_id": cls.czk.id,
        })
        cls.customer = cls.env["res.partner"].create({"name": "Odběratel a.s."})
        cls.env["res.partner.bank"].create({
            "acc_number": "19012333/0300", "partner_id": cls.customer.id,
        })

    def _import(self, data, filename="vypis.okm"):
        wizard = self.env["account.statement.import"].with_context(
            journal_id=self.journal.id
        ).create({
            "statement_file": base64.b64encode(data),
            "statement_filename": filename,
        })
        return wizard.import_file_button()

    def _lines(self):
        return self.env["account.bank.statement.line"].search(
            [("journal_id", "=", self.journal.id)])

    def test_import(self):
        self._import(f.statement(f.transaction()))
        statement = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)])
        self.assertEqual(len(statement), 1)
        self.assertAlmostEqual(statement.balance_start, 10000.0)
        self.assertAlmostEqual(statement.balance_end_real, 11234.5)
        line = statement.line_ids
        self.assertAlmostEqual(line.amount, 1234.5)
        self.assertEqual(line.partner_id, self.customer)
        self.assertIn("VS:20260042", line.payment_ref)
        self.assertEqual(line.transaction_type, "15")
        if "variable_symbol" in line._fields:
            self.assertEqual(line.variable_symbol, "20260042")
            self.assertEqual(line.constant_symbol, "0308")

    def test_reimport_dedup(self):
        data = f.statement(f.transaction())
        self._import(data)
        with self.assertRaises(UserError):
            self._import(data, filename="again.okm")
        self.assertEqual(len(self._lines()), 1)

    def test_non_best_falls_through(self):
        with self.assertRaises(UserError):
            self._import(b"definitely,not,best\n1,2,3\n", filename="x.csv")
