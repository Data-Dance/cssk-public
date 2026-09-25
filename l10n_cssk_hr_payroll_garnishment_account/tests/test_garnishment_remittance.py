# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
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

    def test_the_orders_own_payee_account_reaches_the_entry(self):
        """One bailiff, several cases, different collection accounts.

        The order carries a "Payee Bank Account" domain-restricted to the
        payee for exactly that reason, and the remittance dropped it — so
        ``account_payment_order`` downstream fell back to the payee's default
        account and the money went to the right creditor on the wrong account,
        which for an exekútor means it is not credited to the case.
        """
        # TWO accounts on the same payee, which is the whole point: one
        # bailiff collects for many debtors and tells you which account this
        # case pays into. With only one account the move fills the field in by
        # itself and the test proves nothing.
        default = self.env["res.partner.bank"].create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": self.order.payee_partner_id.id,
        })
        for_this_case = self.env["res.partner.bank"].create({
            "acc_number": "CZ9455000000001011038930",
            "partner_id": self.order.payee_partner_id.id,
        })
        self.order.partner_bank_id = for_this_case
        line = self._line(1000.0)
        line.action_remit()
        self.assertEqual(
            line.move_id.partner_bank_id, for_this_case,
            "the entry must route to the account THIS case collects on, not "
            "the payee's first one")
        self.assertNotEqual(line.move_id.partner_bank_id, default)

    def test_an_accountant_may_remit_but_not_rewrite_the_deduction(self):
        """The ACL exists to let the remittance happen, and no more.

        Granting ``account.group_account_user`` write on the deduction line is
        what the remit flow needs (it sets ``state`` and ``move_id``). Left
        unqualified it would also let anyone who can post an entry change how
        much is being withheld from an employee's wage. Payroll decides the
        deduction; accounting records that it was paid.
        """
        accountant = self.env["res.users"].create({
            "name": "Accountant", "login": "cssk_garnishment_accountant",
            "company_ids": [(6, 0, [self.company.id])],
            "company_id": self.company.id,
            "group_ids": [(6, 0, [
                self.env.ref("account.group_account_user").id,
                self.env.ref("base.group_user").id,
            ])],
        })
        self.assertFalse(accountant.has_group("hr.group_hr_user"),
                         "premise: this user keeps books, not payroll")
        line = self._line(1000.0).with_user(accountant)

        # The workflow the ACL was added for must work end to end.
        line.action_remit()
        self.assertEqual(line.sudo().state, "done")
        self.assertTrue(line.sudo().move_id)

        # Editing the withheld amount must not.
        with self.assertRaises(AccessError):
            self._line(500.0).with_user(accountant).write({"amount": 1.0})

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
