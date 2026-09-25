# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account_fio.tests.common import FioCommon
from odoo.addons.account_fio_base.tests.fio_fixtures import import_response
from odoo.addons.account_fio_base.utils.client import FioUploadUncertain


@tagged("post_install", "-at_install")
class TestFioPaymentOrder(FioCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.method = cls.env["account.payment.method"].search(
            [("code", "=", "fio_xml")], limit=1,
        )
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "Fio",
            "company_id": cls.company.id,
            "payment_method_id": cls.method.id,
            "bank_account_link": "fixed",
            "fixed_journal_id": cls.journal.id,
        })
        cls.czk = cls.env.ref("base.CZK")

    def _order(self, **line_vals):
        order = self.env["account.payment.order"].sudo().create({
            "payment_mode_id": self.mode.id,
            "payment_type": "outbound",
            "journal_id": self.journal.id,
        })
        vals = {
            "order_id": order.id,
            "partner_id": self.supplier.id,
            "partner_bank_id": self.supplier_bank.id,
            "currency_id": self.czk.id,
            "amount_currency": 1234.50,
            "date": "2026-04-25",
            "communication": "Faktura 2026/0042",
            "variable_symbol": "20260042",
        }
        vals.update(line_vals)
        self.env["account.payment.line"].sudo().create(vals)
        return order

    # ------------------------------------------------------------------
    # the file
    # ------------------------------------------------------------------

    def test_generated_file_is_a_fio_import(self):
        order = self._order()
        payload, filename = order.generate_payment_file()
        self.assertTrue(filename.endswith(".xml"))
        root = etree.fromstring(payload)
        self.assertEqual(root.tag, "Import")
        transaction = root.find("Orders/DomesticTransaction")
        self.assertEqual(transaction.findtext("accountFrom"), "2111111111")
        self.assertEqual(transaction.findtext("accountTo"), "2222233333")
        self.assertEqual(transaction.findtext("bankCode"), "2010")
        self.assertEqual(transaction.findtext("amount"), "1234.50")
        self.assertEqual(transaction.findtext("vs"), "20260042")

    def test_symbols_fall_back_to_the_communication(self):
        order = self._order(
            variable_symbol=False, communication="Platba VS:987654 KS:0308",
        )
        root = etree.fromstring(order.generate_payment_file()[0])
        transaction = root.find("Orders/DomesticTransaction")
        self.assertEqual(transaction.findtext("vs"), "987654")
        self.assertEqual(transaction.findtext("ks"), "0308")

    def test_another_payment_method_is_left_alone(self):
        """The override must not swallow ABO or MultiCash orders."""
        order = self._order()
        order.payment_mode_id.payment_method_id = self.env[
            "account.payment.method"
        ].search([("code", "=", "manual")], limit=1)
        self.assertEqual(order.generate_payment_file(), (False, False))

    def test_incomplete_foreign_payment_is_reported_in_full(self):
        foreign = self.env["res.partner"].create({"name": "Amir Khan"})
        foreign_bank = self.env["res.partner.bank"].sudo().create({
            "acc_number": "PK36SCBL0000001123456702",
            "partner_id": foreign.id,
            "company_id": self.company.id,
        })
        order = self._order(
            partner_id=foreign.id,
            partner_bank_id=foreign_bank.id,
            currency_id=self.env.ref("base.USD").id,
            communication="",
        )
        with self.assertRaises(UserError) as caught:
            order.generate_payment_file()
        message = str(caught.exception)
        self.assertIn("BIC", message)
        self.assertIn("platební titul", message)

    def test_platebni_titul_defaults_from_the_partner(self):
        self.supplier.fio_payment_reason = "348"
        order = self._order()
        self.assertEqual(order.payment_line_ids.fio_payment_reason, "348")

    def test_confirmation_refuses_an_order_fio_cannot_take(self):
        """Fail at confirmation, not when somebody is trying to pay."""
        foreign = self.env["res.partner"].create({"name": "Amir Khan"})
        foreign_bank = self.env["res.partner.bank"].sudo().create({
            "acc_number": "PK36SCBL0000001123456702",
            "partner_id": foreign.id,
            "company_id": self.company.id,
        })
        order = self._order(
            partner_id=foreign.id,
            partner_bank_id=foreign_bank.id,
            currency_id=self.env.ref("base.USD").id,
            communication="",
        )
        with self.assertRaises(UserError) as caught:
            order.draft2open()
        self.assertIn("cannot be sent to Fio yet", str(caught.exception))
        self.assertEqual(order.state, "draft")

    def test_a_valid_order_confirms(self):
        order = self._order()
        order.draft2open()
        self.assertEqual(order.state, "open")

    def test_confirmation_ignores_orders_of_another_method(self):
        order = self._order()
        order.payment_mode_id.payment_method_id = self.env[
            "account.payment.method"
        ].search([("code", "=", "manual")], limit=1)
        order.draft2open()
        self.assertEqual(order.state, "open")

    def test_a_non_numeric_variable_symbol_is_refused_at_entry(self):
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self._order(variable_symbol="FA/42")

    def test_a_non_numeric_constant_symbol_is_refused_at_entry(self):
        # Distinct name from the variable-symbol case above. Both were called
        # test_a_non_numeric_symbol_is_refused_at_entry, so this one shadowed
        # the other and the variable_symbol assertion never ran.
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self._order(constant_symbol="12A4")

    def test_an_over_long_symbol_is_TRUNCATED_not_refused(self):
        """Documents behaviour that is arguably wrong, so it cannot change silently.

        ``constant_symbol`` is ``fields.Char(size=4)``, and Odoo truncates on
        write, so the ``len(value) > max_len`` half of ``_check_payment_symbols_cz``
        is unreachable: the constraint only ever sees an already-shortened value.
        A silently shortened VS is a payment that will not match its invoice, so
        this deserves a real refusal — but ``size=`` is declared identically in
        ``account_abo`` and ``account_multicash``, and changing it in one module
        only would make whichever loads last decide. It is one change across the
        three, not a Fio-local fix.
        """
        order = self._order(constant_symbol="12345")
        self.assertEqual(order.payment_line_ids.constant_symbol, "1234")

    def test_the_payload_is_the_generated_attachment(self):
        order = self._generated_order()
        payload, filename = order._fio_payload()
        self.assertTrue(payload.startswith(b"<?xml"))
        self.assertTrue(filename.endswith(".xml"))

    def test_an_ungenerated_order_has_no_payload(self):
        order = self._order()
        with self.assertRaises(UserError):
            order._fio_payload()

    def test_only_a_generated_order_may_be_sent(self):
        order = self._order()
        self.assertFalse(order._fio_can_upload())
        order.draft2open()
        self.assertFalse(order._fio_can_upload())
        order.open2generated()
        self.assertTrue(order._fio_can_upload())

    # ------------------------------------------------------------------
    # sending
    # ------------------------------------------------------------------

    def _generated_order(self):
        order = self._order()
        order.draft2open()
        order.open2generated()
        return order

    def _send(self, order, answer):
        with patch.object(
            type(self.journal), "_fio_call", autospec=True,
            **({"side_effect": answer} if isinstance(answer, Exception)
               else {"return_value": answer}),
        ):
            return order.action_fio_upload()

    def test_accepted_upload(self):
        order = self._generated_order()
        self._send(order, import_response(error_code=0, id_instruction="17048"))
        self.assertEqual(order.fio_upload_state, "sent")
        self.assertEqual(order.fio_id_instruction, "17048")
        self.assertEqual(order.state, "uploaded")

    def test_warnings_still_mean_accepted(self):
        """§6.1: errorCode 2 is "accepted, with warnings".

        Reading it as a failure would have the operator send the batch again,
        and Fio would then hold two of them.
        """
        order = self._generated_order()
        self._send(order, import_response(
            error_code=2, status="warning", id_instruction="17049",
            messages=[("warning", 2, "Měna platby nesouhlasí s měnou účtu")],
        ))
        self.assertEqual(order.fio_upload_state, "sent")
        self.assertEqual(order.state, "uploaded")
        self.assertIn("nesouhlasí", order.message_ids[0].body)

    def test_rejected_upload_stays_sendable(self):
        """The bank's reasons are recorded, not raised.

        A ``UserError`` would roll the transaction back and take the response
        with it, leaving the user with a message and no record of it.
        """
        order = self._generated_order()
        action = self._send(order, import_response(
            error_code=1, status="error", id_instruction="",
            messages=[("error", 100, "Neplatné číslo účtu")],
        ))
        self.assertEqual(action["params"]["type"], "danger")
        self.assertEqual(order.fio_upload_state, "not_sent")
        self.assertEqual(order.state, "generated")
        self.assertIn("Neplatné", order.fio_response)

    def test_a_lost_answer_is_unknown_and_the_state_survives(self):
        """The batch may exist. Nothing may quietly let it be sent twice.

        The state must be WRITTEN, not raised: raising rolls it back, and the
        next click would send a second batch.
        """
        order = self._generated_order()
        action = self._send(order, FioUploadUncertain("read timed out"))
        self.assertEqual(action["params"]["type"], "danger")
        self.assertEqual(order.fio_upload_state, "unknown")
        self.assertEqual(order.state, "generated")

    def test_a_refused_call_raises_without_touching_the_record(self):
        """A 409 or a bad token never reached the bank — nothing to record."""
        from odoo.addons.account_fio_base.utils.client import FioRateLimited

        order = self._generated_order()
        with self.assertRaises(UserError):
            self._send(order, FioRateLimited("wait 30 s"))
        self.assertEqual(order.fio_upload_state, "not_sent")

    def test_an_unknown_upload_cannot_simply_be_retried(self):
        order = self._generated_order()
        order.sudo().fio_upload_state = "unknown"
        with self.assertRaises(UserError) as caught:
            order.action_fio_upload()
        self.assertIn("internet banking", str(caught.exception))

    def test_confirming_the_batch_exists_blocks_resending(self):
        order = self._generated_order()
        order.sudo().fio_upload_state = "unknown"
        order.action_fio_confirm_sent()
        self.assertEqual(order.fio_upload_state, "sent")
        with self.assertRaises(UserError):
            order.action_fio_upload()

    def test_confirming_the_batch_is_absent_allows_resending(self):
        order = self._generated_order()
        order.sudo().write({
            "fio_upload_state": "unknown", "fio_id_instruction": "17050",
        })
        order.action_fio_confirm_not_sent()
        self.assertEqual(order.fio_upload_state, "not_sent")
        self.assertFalse(order.fio_id_instruction)

    def test_sending_twice_is_refused(self):
        order = self._generated_order()
        self._send(order, import_response(id_instruction="17051"))
        with self.assertRaises(UserError) as caught:
            order.action_fio_upload()
        self.assertIn("17051", str(caught.exception))
