# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentSymbols(AccountTestInvoicingCommon):

    def _invoice(self, move_type="out_invoice", **extra):
        vals = {
            "move_type": move_type,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.from_string("2026-07-01"),
            "invoice_line_ids": [
                Command.create({
                    "product_id": self.product_a.id,
                    "quantity": 1,
                    "price_unit": 100.0,
                })
            ],
        }
        vals.update(extra)
        return self.env["account.move"].create(vals)

    # ------------------------------------------------------------------
    # account.move
    # ------------------------------------------------------------------
    def test_vs_from_invoice_name_capped_at_10_digits(self):
        invoice = self._invoice()
        invoice.action_post()
        digits = "".join(ch for ch in invoice.name if ch.isdigit())
        self.assertEqual(invoice.l10n_cssk_variable_symbol, digits[-10:])
        self.assertTrue(len(invoice.l10n_cssk_variable_symbol) <= 10)

    def test_vs_vendor_bill_from_ref(self):
        bill = self._invoice(move_type="in_invoice", ref="FA-2026/00042")
        self.assertEqual(bill.l10n_cssk_variable_symbol, "202600042")

    def test_refund_vs_policy_own_and_origin(self):
        invoice = self._invoice()
        invoice.action_post()
        reversal = invoice._reverse_moves(cancel=False)
        reversal.action_post()
        # default policy: the credit note carries its own number
        own_digits = "".join(ch for ch in reversal.name if ch.isdigit())[-10:]
        self.assertEqual(reversal.l10n_cssk_variable_symbol, own_digits)

        self.env.company.l10n_cssk_refund_vs_policy = "origin"
        reversal2 = invoice._reverse_moves(cancel=False)
        self.assertEqual(
            reversal2.l10n_cssk_variable_symbol,
            invoice.l10n_cssk_variable_symbol,
        )

    def test_default_constant_symbol_on_customer_documents(self):
        self.env.company.l10n_cssk_default_constant_symbol = "0308"
        invoice = self._invoice()
        self.assertEqual(invoice.l10n_cssk_constant_symbol, "0308")
        bill = self._invoice(move_type="in_invoice", ref="X1")
        self.assertFalse(bill.l10n_cssk_constant_symbol)

    def test_symbol_validation(self):
        invoice = self._invoice()
        with self.assertRaises(ValidationError):
            invoice.l10n_cssk_constant_symbol = "03080"  # 5 > 4 digits
        with self.assertRaises(ValidationError):
            invoice.l10n_cssk_specific_symbol = "12A4"  # non-digit
        invoice.l10n_cssk_specific_symbol = "1234567890"  # ok

    def test_payment_reference_use_vs_toggle(self):
        self.env.company.l10n_cssk_payment_reference_use_vs = True
        invoice = self._invoice()
        invoice.action_post()
        self.assertEqual(
            invoice.payment_reference, invoice.l10n_cssk_variable_symbol
        )

    # ------------------------------------------------------------------
    # account.bank.statement.line
    # ------------------------------------------------------------------
    def _st_line(self, **vals):
        base = {
            "journal_id": self.company_data["default_journal_bank"].id,
            "date": fields.Date.from_string("2026-07-10"),
            "payment_ref": "test transfer",
            "amount": 100.0,
        }
        base.update(vals)
        return self.env["account.bank.statement.line"].create(base)

    def test_st_line_explicit_symbol_prefixes_payment_ref(self):
        line = self._st_line(variable_symbol="20260042")
        self.assertEqual(line.variable_symbol, "20260042")
        self.assertEqual(line.payment_ref, "20260042 - test transfer")

    def test_st_line_no_double_prefix(self):
        line = self._st_line(
            variable_symbol="20260042",
            payment_ref="20260042 - test transfer",
        )
        self.assertEqual(line.payment_ref, "20260042 - test transfer")

    def test_st_line_extract_from_transaction_details(self):
        # upstream PR #275611 key, nested one level down
        line = self._st_line(
            transaction_details={
                "remittance": {"variable_code": "990011", "ks": "0308"},
            },
        )
        self.assertEqual(line.variable_symbol, "990011")
        self.assertEqual(line.constant_symbol, "0308")
        self.assertTrue(line.payment_ref.startswith("990011 - "))

    def test_st_line_extract_from_payment_ref_tokens(self):
        line = self._st_line(payment_ref="Payment /VS/12345/KS/0008/SS/777")
        self.assertEqual(line.variable_symbol, "12345")
        self.assertEqual(line.constant_symbol, "0008")
        self.assertEqual(line.specific_symbol, "777")

        line2 = self._st_line(payment_ref="uhrada VS: 4455 dakujeme")
        self.assertEqual(line2.variable_symbol, "4455")

    def test_st_line_symbols_only_in_the_end_to_end_id(self):
        """OCA CAMT puts EndToEndId in ref; the label is free text."""
        cases = [
            ("?/VS53155/SS/KS", ("53155", False, False)),  # Fio
            ("/VS53101/SS/KS", ("53101", False, False)),
            ("/VS26001001/SS55510022/KS", ("26001001", "55510022", False)),
            ("/VS26004101/SS0/KS0008", ("26004101", False, "0008")),
        ]
        for ref, (vs, ss, ks) in cases:
            line = self._st_line(payment_ref="Syntetická úhrada objednávky", ref=ref)
            self.assertEqual(
                (line.variable_symbol, line.specific_symbol, line.constant_symbol),
                (vs, ss, ks), ref)
            self.assertTrue(line.payment_ref.startswith(vs + " - "), ref)

    def test_st_line_label_wins_over_ref(self):
        line = self._st_line(payment_ref="VS 111", ref="/VS222/SS/KS")
        self.assertEqual(line.variable_symbol, "111")

    def test_st_line_card_order_number_is_not_a_vs(self):
        """Tatra banka CardPay: EndToEndId is the e-shop order number."""
        line = self._st_line(payment_ref="CardPay", ref="000053228")
        self.assertFalse(line.variable_symbol)
        line = self._st_line(payment_ref="Platba", ref="2428500179")
        self.assertFalse(line.variable_symbol)

    def test_st_line_symbols_from_the_narration(self):
        line = self._st_line(payment_ref="x", narration="<p>/VS998877/SS/KS</p>")
        self.assertEqual(line.variable_symbol, "998877")

    def test_st_line_no_symbols_noop(self):
        line = self._st_line(payment_ref="plain label without symbols")
        self.assertFalse(line.variable_symbol)
        self.assertEqual(line.payment_ref, "plain label without symbols")

    # ------------------------------------------------------------------
    # QR context
    # ------------------------------------------------------------------
    def test_qr_context_symbols(self):
        invoice = self._invoice()
        invoice.l10n_cssk_constant_symbol = "0308"
        invoice.action_post()
        captured = {}

        def spy(bank, *args, **kwargs):
            captured["symbols"] = bank.env.context.get("cssk_payment_symbols")
            return None

        self.patch(
            type(self.env["res.partner.bank"]), "build_qr_code_base64", spy
        )
        invoice.partner_bank_id = self.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": self.env.company.partner_id.id,
        })
        invoice._generate_qr_code(silent_errors=True)
        if captured.get("symbols") is not None:
            self.assertEqual(
                captured["symbols"].get("variable_symbol"),
                invoice.l10n_cssk_variable_symbol,
            )
            self.assertEqual(captured["symbols"].get("constant_symbol"), "0308")

    # ------------------------------------------------------------------
    # account.payment
    # ------------------------------------------------------------------
    def _register_payment(self, moves):
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=moves.ids
        ).create({})
        return wizard._create_payments()

    def test_payment_symbols_from_single_bill(self):
        bill = self._invoice(move_type="in_invoice", ref="FA-2026/00042")
        bill.l10n_cssk_constant_symbol = "0308"
        bill.action_post()
        payment = self._register_payment(bill)
        self.assertEqual(payment.l10n_cssk_variable_symbol, "202600042")
        self.assertEqual(payment.l10n_cssk_constant_symbol, "0308")

    def test_payment_symbols_dropped_on_mixed_batch(self):
        bill_a = self._invoice(move_type="in_invoice", ref="FA-1")
        bill_b = self._invoice(move_type="in_invoice", ref="FA-2")
        (bill_a + bill_b).action_post()
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=(bill_a + bill_b).ids
        ).create({"group_payment": True})
        payments = wizard._create_payments()
        self.assertEqual(len(payments), 1)
        self.assertFalse(payments.l10n_cssk_variable_symbol)

    def test_payment_symbol_validation(self):
        bill = self._invoice(move_type="in_invoice", ref="FA-1")
        bill.action_post()
        payment = self._register_payment(bill)
        with self.assertRaises(ValidationError):
            payment.l10n_cssk_constant_symbol = "12345"
