from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAdvanceStatementMatch(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("sales_team.group_sale_manager")
        company = cls.env.company
        Account = cls.env["account.account"]
        # receivable type per the localization specs: the clearing account is
        # the receivable side of the tax document (payment_term line)
        cls.clearing = Account.create({
            "code": "324001",
            "name": "Advance clearing",
            "account_type": "asset_receivable",
            "reconcile": True,
        })
        cls.net_advance = Account.create({
            "code": "324000",
            "name": "Advances received",
            "account_type": "liability_current",
        })
        cls.adv_journal = cls.env["account.journal"].create({
            "name": "Advance Tax Documents",
            "code": "TDADV",
            "type": "general",
        })
        company.advance_invoice_journal_id = cls.adv_journal
        company.advance_received_account_id = cls.clearing
        company.advance_tax_doc_account_id = cls.net_advance
        company.advance_invoice_auto_match_statement = True
        company.advance_invoice_auto_tax_doc = "post"

        cls.bank_journal = cls.company_data["default_journal_bank"]
        outstanding = Account.create({
            "code": "OUTREC",
            "name": "Outstanding Receipts",
            "account_type": "asset_current",
            "reconcile": True,
        })
        cls.bank_journal.inbound_payment_method_line_ids[
            :1
        ].payment_account_id = outstanding

        cls.provider = cls.env["payment.provider"].create({
            "name": "Offline",
            "code": "none",
            "company_id": company.id,
        })

    def _advance(self, price=1000.0, partner=None):
        return self.env["sale.order"].create({
            "partner_id": (partner or self.partner_a).id,
            "is_advance_invoice": True,
            "order_line": [
                Command.create({
                    "product_id": self.product_a.id,
                    "product_uom_qty": 1,
                    "price_unit": price,
                })
            ],
        })

    def _st_line(self, amount, payment_ref, **vals):
        base = {
            "journal_id": self.bank_journal.id,
            "date": fields.Date.from_string("2026-07-10"),
            "payment_ref": payment_ref,
            "amount": amount,
        }
        base.update(vals)
        return self.env["account.bank.statement.line"].create(base)

    # ------------------------------------------------------------------
    def test_exact_match_full_payment_with_posted_tax_doc(self):
        advance = self._advance()
        line = self._st_line(advance.amount_total, f"payment {advance.name}")

        payment = line._cssk_try_match_advance()
        self.assertTrue(payment)
        self.assertEqual(payment.amount, advance.amount_total)
        self.assertEqual(payment.destination_account_id, self.clearing)

        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")
        self.assertEqual(advance.state, "sale")
        self.assertTrue(line.is_reconciled)
        self.assertEqual(line.partner_id, self.partner_a)

        # tax document created, posted, in the advance journal, and the
        # clearing account nets to zero (payment leg vs tax doc leg)
        tax_doc = advance.invoice_ids.filtered(
            lambda move: move.journal_id == self.adv_journal
        )
        self.assertEqual(len(tax_doc), 1)
        self.assertEqual(tax_doc.state, "posted")
        clearing_lines = (
            payment.move_id + tax_doc
        ).line_ids.filtered(lambda aml: aml.account_id == self.clearing)
        self.assertTrue(all(clearing_lines.mapped("reconciled")))
        self.assertEqual(
            advance.advance_invoice_accounting_status, "accounted"
        )

    def test_digits_match_requires_exact_amount(self):
        advance = self._advance()
        digits = "".join(ch for ch in advance.name if ch.isdigit())
        # bare digit run, no VS marker (a "VS 123" token would be extracted
        # into the structured variable_symbol field by the symbols module
        # and rightly trusted for partial amounts)
        partial = self._st_line(advance.amount_total / 2, f"uhrada {digits}")
        self.assertFalse(partial._cssk_try_match_advance())

        full = self._st_line(advance.amount_total, f"uhrada {digits}")
        self.assertTrue(full._cssk_try_match_advance())
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")

    def test_exact_match_allows_partial_payment(self):
        advance = self._advance()
        line = self._st_line(advance.amount_total / 2, advance.name)
        self.assertTrue(line._cssk_try_match_advance())
        self.assertEqual(
            advance.advance_invoice_payment_status, "paid_partially"
        )
        self.assertTrue(line.is_reconciled)

    def test_overpayment_is_skipped(self):
        advance = self._advance()
        line = self._st_line(
            advance.amount_total + 100.0, f"payment {advance.name}"
        )
        self.assertFalse(line._cssk_try_match_advance())
        self.assertFalse(line.is_reconciled)

    def test_variable_symbol_field_preferred_when_present(self):
        advance = self._advance()
        digits = "".join(ch for ch in advance.name if ch.isdigit())
        line = self._st_line(advance.amount_total / 2, "no useful label")
        if "variable_symbol" not in line._fields:
            self.skipTest("no variable_symbol field installed")
        line.variable_symbol = digits.lstrip("0") or digits
        # vs tier allows partial amounts (structured symbol = strong signal)
        self.assertTrue(line._cssk_try_match_advance())
        self.assertEqual(
            advance.advance_invoice_payment_status, "paid_partially"
        )

    def test_ambiguous_digits_bail_out(self):
        advance_a = self._advance()
        advance_b = self._advance()
        # craft a label matching both names as exact tokens
        line = self._st_line(
            advance_a.amount_total, f"{advance_a.name} {advance_b.name}"
        )
        self.assertFalse(line._cssk_try_match_advance())

    def test_partner_mismatch_excludes_candidate(self):
        advance = self._advance(partner=self.partner_a)
        line = self._st_line(
            advance.amount_total,
            f"payment {advance.name}",
            partner_id=self.partner_b.id,
        )
        self.assertFalse(line._cssk_try_match_advance())

    def test_auto_flag_off_no_match(self):
        self.env.company.advance_invoice_auto_match_statement = False
        advance = self._advance()
        line = self._st_line(advance.amount_total, advance.name)
        self.assertFalse(line._cssk_try_match_advance())

    def test_tax_doc_draft_mode(self):
        self.env.company.advance_invoice_auto_tax_doc = "draft"
        advance = self._advance()
        line = self._st_line(advance.amount_total, advance.name)
        self.assertTrue(line._cssk_try_match_advance())
        tax_doc = advance.invoice_ids.filtered(
            lambda move: move.journal_id == self.adv_journal
        )
        self.assertEqual(tax_doc.state, "draft")

    def test_cron_processes_lines(self):
        advance = self._advance()
        line = self._st_line(advance.amount_total, advance.name)
        self.env[
            "account.bank.statement.line"
        ]._cron_match_advance_statement_lines()
        self.assertTrue(line.is_reconciled)
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")

    def test_wizard_suggests_and_applies(self):
        self.env.company.advance_invoice_auto_tax_doc = "none"
        advance = self._advance()
        line = self._st_line(advance.amount_total, advance.name)
        wizard = (
            self.env["advance.statement.match.wizard"]
            .with_context(
                active_model="account.bank.statement.line",
                active_id=line.id,
            )
            .create({})
        )
        self.assertEqual(wizard.order_id, advance)
        wizard.action_apply()
        self.assertTrue(line.is_reconciled)
        self.assertEqual(advance.advance_invoice_payment_status, "paid_fully")
        self.assertEqual(
            advance.advance_invoice_accounting_status, "waiting"
        )
