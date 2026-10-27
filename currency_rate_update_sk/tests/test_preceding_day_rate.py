# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""§ 24 ods. 2 písm. a) ZoÚ / § 26 ods. 1 ZDPH: the rate of the preceding day."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

# Units of USD per EUR, each stored under the day the ECB announced it.
# 2026-03-06 is a Friday; nothing is announced on the weekend.
RATES = {
    "2026-03-04": 1.05,
    "2026-03-05": 1.10,
    "2026-03-06": 1.20,
    "2026-03-09": 1.30,
}


@tagged("post_install", "-at_install")
class TestSkPrecedingDayRate(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.usd = cls.setup_other_currency("USD", rates=list(RATES.items()))

    def _bill(self, invoice_date, taxable_supply_date=None, company=None):
        company = company or self.company
        vals = {
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": invoice_date,
            "currency_id": self.usd.id,
            "company_id": company.id,
            "invoice_line_ids": [
                Command.create({"name": "x", "quantity": 1, "price_unit": 120.0,
                                "tax_ids": [Command.clear()]})
            ],
        }
        if taxable_supply_date:
            vals["taxable_supply_date"] = taxable_supply_date
        return self.env["account.move"].with_company(company).create(vals)

    def test_a_document_takes_the_rate_announced_the_day_before(self):
        bill = self._bill("2026-03-06")
        self.assertAlmostEqual(bill.invoice_currency_rate, 1.10)
        self.assertAlmostEqual(bill.amount_total_signed, -120.0 / 1.10, 2)

    def test_after_a_weekend_the_last_announced_rate_applies(self):
        for day in ("2026-03-07", "2026-03-08", "2026-03-09"):
            self.assertAlmostEqual(
                self._bill(day).invoice_currency_rate, 1.20, msg=day)

    def test_the_day_of_supply_decides_for_vat(self):
        """§ 26 ods. 1: the day before the tax liability arises (§ 19 ods. 1)."""
        bill = self._bill("2026-03-10", taxable_supply_date="2026-03-06")
        self.assertAlmostEqual(bill.invoice_currency_rate, 1.10)

    def test_a_journal_entry_line_follows_the_rule(self):
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-03-06",
            "company_id": self.company.id,
            "line_ids": [
                Command.create({
                    "account_id": self.company_data["default_account_receivable"].id,
                    "partner_id": self.partner_a.id,
                    "currency_id": self.usd.id,
                    "amount_currency": 110.0,
                }),
                Command.create({
                    "account_id": self.company_data["default_account_revenue"].id,
                    "currency_id": self.usd.id,
                    "amount_currency": -110.0,
                }),
            ],
        })
        line = move.line_ids.filtered(lambda l: l.amount_currency > 0)
        self.assertAlmostEqual(line.currency_rate, 1.10)
        self.assertAlmostEqual(line.balance, 100.0)

    def test_a_payment_follows_the_rule(self):
        payment = self.env["account.payment"].create({
            "payment_type": "outbound",
            "partner_type": "supplier",
            "partner_id": self.partner_a.id,
            "amount": 110.0,
            "currency_id": self.usd.id,
            "date": "2026-03-06",
            "journal_id": self.company_data["default_journal_bank"].id,
        })
        self.assertAlmostEqual(payment.amount_company_currency_signed, -100.0)
        payment.action_post()
        liquidity = payment._seek_for_lines()[0]
        self.assertAlmostEqual(liquidity.balance, -100.0)

    def test_the_balance_sheet_day_keeps_its_own_rate(self):
        """§ 24 ods. 2 písm. b): a conversion outside a document is untouched.

        The year-end revaluation asks res.currency directly for the rate of
        the balance-sheet day; shifting every conversion would have revalued
        at the day before.
        """
        eur = self.company.currency_id
        self.assertAlmostEqual(
            eur._convert(1.0, self.usd, self.company, "2026-03-06", round=False),
            1.20,
        )

    def test_a_company_outside_slovakia_keeps_odoo_s_rule(self):
        belgium = self.env.ref("base.be")
        self.company.write({
            "country_id": belgium.id,
            "account_fiscal_country_id": belgium.id,
        })
        self.assertFalse(self.company._l10n_sk_uses_preceding_day_rate())
        self.assertAlmostEqual(self._bill("2026-03-06").invoice_currency_rate, 1.20)
