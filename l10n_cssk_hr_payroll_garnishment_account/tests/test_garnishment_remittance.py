# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGarnishmentRemittance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "Remit CZ", "country_id": cls.env.ref("base.cz").id}
        )
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env["account.chart.template"].try_loading(
            "generic_coa", company=cls.company, install_demo=False
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Payroll",
                "code": "PAYRL",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.liability = cls.env["account.account"].create(
            {
                "name": "Garnishment liability",
                "code": "379100",
                "account_type": "liability_current",
                "company_ids": [(4, cls.company.id)],
            }
        )
        cls.company.write(
            {
                "l10n_cssk_garnishment_journal_id": cls.journal.id,
                "l10n_cssk_garnishment_account_id": cls.liability.id,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Dlužník", "company_id": cls.company.id}
        )
        cls.bailiff = cls.env["res.partner"].create({"name": "Exekutor"})
        cls.order = cls.env["hr.wage.garnishment"].create(
            {
                "case_number": "123 EX 456/2026",
                "employee_id": cls.employee.id,
                "company_id": cls.company.id,
                "claim_class": "ordinary",
                "date_delivered": "2026-01-10",
                "total_amount": 100000.0,
                "bailiff_partner_id": cls.bailiff.id,
                "state": "running",
            }
        )

    def _line(self, amount=1000.0):
        return self.env["hr.wage.garnishment.line"].create(
            {
                "garnishment_id": self.order.id,
                "employee_id": self.employee.id,
                "payslip_ref": "hr.payslip,1",
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "amount": amount,
                "amount_first_third": amount,
            }
        )

    def test_remittance_creates_balanced_payable(self):
        line = self._line()
        line.action_remit()
        move = line.move_id
        self.assertTrue(move)
        self.assertEqual(move.state, "posted")
        self.assertEqual(line.state, "done")
        debit = move.line_ids.filtered(lambda ml: ml.debit)
        credit = move.line_ids.filtered(lambda ml: ml.credit)
        self.assertEqual(debit.account_id, self.liability)
        self.assertEqual(debit.debit, 1000.0)
        self.assertEqual(credit.credit, 1000.0)
        # The credit is a payable owed to the bailiff — this is what the
        # payment order picks up to actually send the money.
        self.assertEqual(credit.partner_id, self.bailiff)
        self.assertEqual(credit.account_id.account_type, "liability_payable")

    def test_case_number_becomes_the_variable_symbol(self):
        line = self._line()
        line.action_remit()
        self.assertEqual(line.move_id.l10n_cssk_variable_symbol, "1234562026")

    def test_remitting_twice_is_a_no_op(self):
        line = self._line()
        line.action_remit()
        move = line.move_id
        with self.assertRaises(UserError):
            line.action_remit()
        self.assertEqual(line.move_id, move)

    def test_missing_configuration_is_reported(self):
        self.company.l10n_cssk_garnishment_account_id = False
        line = self._line()
        with self.assertRaises(UserError):
            line.action_remit()

    def test_wizard_collects_the_period(self):
        self._line(600.0)
        self._line(400.0)
        wizard = self.env["hr.wage.garnishment.remittance"].create(
            {"company_id": self.company.id, "date_to": "2026-03-31"}
        )
        self.assertEqual(wizard.line_count, 2)
        self.assertEqual(wizard.total_amount, 1000.0)
        wizard.action_remit()
        # Both deductions belong to one order, so they share a single entry
        # carrying that case's variable symbol.
        move = wizard.line_ids.move_id
        self.assertEqual(len(move), 1)
        self.assertEqual(sum(move.line_ids.mapped("debit")), 1000.0)
