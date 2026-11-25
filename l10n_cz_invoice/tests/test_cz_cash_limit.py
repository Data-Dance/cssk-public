# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Zákon č. 254/2004 Sb., § 4: 270 000 Kč per payer, payee and day."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzCashLimit(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.cash = cls.company_data["default_journal_cash"]
        cls.bank = cls.company_data["default_journal_bank"]
        cls.partner = cls.env["res.partner"].create({"name": "Odběratel"})
        cls.other = cls.env["res.partner"].create({"name": "Jiný odběratel"})

    def _payment(self, amount, journal=None, partner=None, day="2026-03-10",
                 payment_type="inbound", post=True, **vals):
        payment = self.env["account.payment"].create(dict({
            "payment_type": payment_type,
            "partner_type": ("customer" if payment_type == "inbound"
                             else "supplier"),
            "partner_id": (partner or self.partner).id,
            "journal_id": (journal or self.cash).id,
            "amount": amount, "date": day}, **vals))
        if post:
            payment.action_post()
        return payment

    def test_one_payment_at_the_limit_and_above_it(self):
        """§ 4 odst. 1: a payment "jejíž výše překračuje částku 270000 Kč"."""
        self.assertFalse(self._payment(270000.0).l10n_cz_cash_limit_warning)
        over = self._payment(270000.01, partner=self.other)
        self.assertTrue(over.l10n_cz_cash_limit_warning)
        self.assertIn("254/2004", over.l10n_cz_cash_limit_warning)

    def test_the_payments_of_one_day_are_added_together(self):
        """§ 4 odst. 4: every payment between the same two on one calendar
        day counts, whatever it pays for."""
        self._payment(150000.0)
        second = self._payment(130000.0, post=False)
        self.assertTrue(second.l10n_cz_cash_limit_warning,
                        "150 000 + 130 000 on one day is above the limit")
        self.assertIn("280000", second.l10n_cz_cash_limit_warning)

    def test_another_day_another_partner_another_direction_do_not_add(self):
        self._payment(150000.0)
        self.assertFalse(self._payment(
            130000.0, day="2026-03-11", post=False).l10n_cz_cash_limit_warning)
        self.assertFalse(self._payment(
            130000.0, partner=self.other,
            post=False).l10n_cz_cash_limit_warning)
        self.assertFalse(self._payment(
            130000.0, payment_type="outbound",
            post=False).l10n_cz_cash_limit_warning)

    def test_a_child_contact_is_the_same_payee(self):
        self.partner.is_company = True
        contact = self.env["res.partner"].create({
            "name": "Pokladní", "parent_id": self.partner.id})
        self._payment(150000.0)
        self.assertTrue(self._payment(
            130000.0, partner=contact, post=False).l10n_cz_cash_limit_warning)

    def test_a_bank_payment_does_not_count_and_does_not_warn(self):
        self._payment(150000.0, journal=self.bank)
        self.assertFalse(self._payment(
            130000.0, post=False).l10n_cz_cash_limit_warning)
        self.assertFalse(self._payment(
            500000.0, journal=self.bank, partner=self.other,
            post=False).l10n_cz_cash_limit_warning)

    def test_a_foreign_payment_counts_at_the_rate_of_its_day(self):
        """§ 4 odst. 3."""
        eur = self.setup_other_currency(
            "EUR", rates=[("2026-01-01", 0.04), ("2026-03-10", 0.05)])
        # 13 000 EUR at 20 Kč on the day = 260 000 Kč, at 25 Kč it would be
        # 325 000 Kč
        payment = self._payment(13000.0, currency_id=eur.id, post=False)
        self.assertFalse(payment.l10n_cz_cash_limit_warning)
        payment = self._payment(14000.0, currency_id=eur.id, post=False)
        self.assertTrue(payment.l10n_cz_cash_limit_warning)

    def test_the_register_wizard_warns_before_the_payment_exists(self):
        self._payment(150000.0, day="2026-03-12")
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "invoice_date": "2026-03-01",
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 130000.0,
                "tax_ids": [Command.clear()]})]})
        invoice.action_post()
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids).create({
                "journal_id": self.cash.id, "payment_date": "2026-03-12"})
        self.assertTrue(wizard.l10n_cz_cash_limit_warning)
        wizard.journal_id = self.bank
        self.assertFalse(wizard.l10n_cz_cash_limit_warning)

    def test_a_cash_statement_line_counts_and_notes_the_warning(self):
        self._payment(150000.0)
        line = self.env["account.bank.statement.line"].create({
            "journal_id": self.cash.id, "date": "2026-03-10",
            "payment_ref": "hotově", "amount": 130000.0,
            "partner_id": self.partner.id})
        self.assertTrue(line.l10n_cz_cash_limit_warning)
        self.assertTrue(line.move_id.message_ids.filtered(
            lambda m: "254/2004" in (m.body or "")))
        deposit = self.env["account.bank.statement.line"].create({
            "journal_id": self.cash.id, "date": "2026-03-10",
            "payment_ref": "odvod do banky", "amount": -500000.0,
            "partner_id": self.company.partner_id.id})
        self.assertFalse(deposit.l10n_cz_cash_limit_warning,
                         "§ 2 odst. 2 písm. a): a deposit is no payment")

    def test_a_company_that_is_not_czech_is_not_warned(self):
        self.company.account_fiscal_country_id = self.env.ref("base.sk")
        self.assertFalse(self._payment(
            900000.0, post=False).l10n_cz_cash_limit_warning)
