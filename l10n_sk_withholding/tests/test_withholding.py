# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from copy import deepcopy
from datetime import date
import hashlib
from pathlib import Path
import re
from unittest.mock import patch

from lxml import etree
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import file_path
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from ..deadline4311 import regular_deadline
from .. import wire4311

MODEL = "l10n.sk.withholding"


@tagged("post_install", "-at_install")
class TestWithholdingNative(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, "lang": "en_US"})
        cls.company = cls.company_data["company"]
        cls.company.write(
            {
                "company_registry": "36000001",
                "l10n_sk_dic": "2020000000",
                "street": "Testovacia1",
                "zip": "85110",
                "city": "Bratislava",
                "vat": False,
            }
        )
        cls.general = cls.company_data["default_journal_misc"]
        cls.bank = cls.company_data["default_journal_bank"].default_account_id
        cls.recipient = cls.env["res.partner"].create(
            {
                "name": "Žofia Šťastná",
                "street": "Testovacia2",
                "zip": "85110",
                "city": "Bratislava",
                "country_id": cls.env.ref("base.sk").id,
            }
        )

        def account(code, kind="liability_current"):
            result = cls.env["account.account"].search(
                [("company_ids", "in", cls.company.id), ("code", "=", code)], limit=1
            )
            return result or cls.env["account.account"].create(
                {
                    "code": code,
                    "name": "Synthetic " + code,
                    "account_type": kind,
                    "company_ids": [Command.set(cls.company.ids)],
                }
            )

        cls.dividend, cls.tax, cls.profit = (
            account("364900"),
            account("342900"),
            account("428900", "equity"),
        )
        cls.capital = account("411900", "equity")
        cls.reserve = account("421900", "equity")
        cls.author_payable = account("379900")
        cls.expense = account("518900", "expense")
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Synthetic4311 accountant",
                "login": "synthetic4311-accountant",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "group_ids": [
                    Command.set(
                        cls.env.ref(
                            "l10n_cssk_submission_base.group_cssk_submission_user"
                        ).ids
                    )
                ],
            }
        )

    def entry(self, title, rows, day):
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": self.general.id,
                "date": day,
                "ref": "Synthetic4311 " + title,
                "line_ids": [
                    Command.create(
                        {
                            "name": title,
                            "account_id": account.id,
                            "debit": max(value, 0),
                            "credit": max(-value, 0),
                            "partner_id": self.recipient.id
                            if account != self.bank
                            else False,
                        }
                    )
                    for account, value in rows
                ],
            }
        )
        move.action_post()
        return move

    def notice(self, paid=True, remitted=True, withholding_day="2026-05-20"):
        self.entry(
            "opening balances",
            [
                (self.bank, 27000),
                (self.capital, -5000),
                (self.reserve, -500),
                (self.profit, -21500),
            ],
            "2026-01-01",
        )
        decision = self.entry(
            "reviewed distribution",
            [(self.profit, 21500), (self.dividend, -21500)],
            "2026-05-10",
        )
        tax = self.entry(
            "actual withholding",
            [(self.dividend, 1700), (self.tax, -1700)],
            withholding_day,
        )
        payout = self.entry(
            "actual net dividend",
            [(self.dividend, 19800), (self.bank, -19800)],
            "2026-05-20",
        )
        transfer = (
            self.entry(
                "actual tax transfer",
                [(self.tax, 1700), (self.bank, -1700)],
                "2026-06-15",
            )
            if remitted
            else False
        )
        events = []
        for gross, period, withheld in ((6500, "2024", 650), (15000, "2025", 1050)):
            events.append(
                Command.create(
                    {
                        "partner_id": self.recipient.id,
                        "first_name": "Žofia",
                        "last_name": "Šťastná",
                        "birth_number": "0051011235",
                        "gross": gross,
                        "profit_period_start": period + "-01-01",
                        "profit_period_end": period + "-12-31",
                        "distribution_line_id": decision.line_ids.filtered(
                            lambda line: line.account_id == self.dividend
                        ).id,
                        "withholding_line_id": tax.line_ids.filtered(
                            lambda line: line.account_id == self.tax
                        ).id,
                        "payment_line_id": payout.line_ids.filtered(
                            lambda line: line.account_id == self.dividend
                        ).id,
                        "remittance_ids": [
                            Command.create(
                                {
                                    "line_id": transfer.line_ids.filtered(
                                        lambda line: line.account_id == self.tax
                                    ).id,
                                    "actual_on": "2026-06-15",
                                    "amount": withheld,
                                    "source_reference": "Synthetic actual tax transfer",
                                    "reviewed": True,
                                }
                            )
                        ]
                        if transfer
                        else [],
                        "payment_reviewed": paid,
                        "source_reference": "Synthetic reviewed decision, bank statement and tax transfer",
                        "decision_on": "2026-05-10",
                        "paid_on": "2026-05-20",
                    }
                )
            )
        return self.env[MODEL].create(
            {
                "company_id": self.company.id,
                "period": "2026-05-01",
                "prepared_on": "2026-06-15",
                "filing_on": "2026-06-15",
                "prepared_by": "Synthetic preparer",
                "resident_scope_reviewed": True,
                "dividend_account_id": self.dividend.id,
                "tax_account_id": self.tax.id,
                "event_ids": events,
            }
        )

    def test_fs_example_uses_native_gl_shared_pipeline_and_ordinary_accountant(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        xml = base64.b64decode(notice.xml_attachment_id.datas)
        root = etree.fromstring(xml)
        self.assertEqual(
            root.findtext("hlavicka/suhrnneUdaje/spolu04/danZrazena"), "1700.00"
        )
        self.assertEqual(
            root.findtext("hlavicka/suhrnneUdaje/spolu04/danOdvedena"), "1700.00"
        )
        notice.action_submit()
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id, notice.xml_attachment_id)
        self.assertTrue(notice.submission_ids)
        self.assertEqual(len(notice.source_history), 1)
        self.assertFalse(self.operator.has_group("base.group_system"))

    def test_reversed_payment_cannot_be_reported_as_paid_income(self):
        notice = self.notice()
        move = notice.event_ids[0].payment_line_id.move_id
        move._reverse_moves(cancel=True)
        with self.assertRaisesRegex(UserError, "unreversed"):
            notice.action_compute_lines()

    def test_resident_scope_must_cover_the_complete_month(self):
        notice = self.notice()
        notice.resident_scope_reviewed = False
        with self.assertRaisesRegex(UserError, "other resident withholding titles"):
            notice.action_compute_lines()
        notice.resident_scope_reviewed = True
        notice.action_compute_lines()
        self.assertTrue(notice.payload["resident_scope_reviewed"])

    def test_schema_pin_and_exported_storage_are_guarded(self):
        notice = self.notice()
        notice.action_compute_lines()
        with patch.object(wire4311, "SCHEMA_SHA256", "0" * 64):
            with self.assertRaisesRegex(UserError, "schema changed"):
                notice.action_export_xml()
        notice.action_export_xml()
        attachment = notice.xml_attachment_id
        content = attachment.raw
        with self.assertRaisesRegex(UserError, "immutable"):
            attachment.write({"store_fname": "not-the-retained-file"})
        attachment.write({"raw": content})
        self.assertEqual(attachment.raw, content)

    def test_late_filing_warning_and_evidenced_authority_deadline(self):
        notice = self.notice()
        notice.filing_on = "2026-07-01"
        notice.action_compute_lines()
        self.assertTrue(
            any(
                "after its applicable deadline" in str(message.body)
                for message in notice.message_ids
            )
        )
        notice.action_reset_to_draft()
        notice.authority_deadline = "2026-07-15"
        with self.assertRaisesRegex(UserError, "actual decision"):
            notice.action_compute_lines()
        notice.authority_deadline_reference = (
            "Synthetic actual authority decision under section 43(11)"
        )
        notice.action_compute_lines()
        self.assertEqual(notice.payload["deadline"], "2026-07-15")

    def test_deadline_working_days_and_2026_holiday_exception(self):
        for period, expected in [
            ("2026-05-01", "2026-06-15"),
            ("2026-07-01", "2026-08-17"),
            ("2026-08-01", "2026-09-15"),
            ("2027-08-01", "2027-09-16"),
            ("2033-03-01", "2033-04-19"),
        ]:
            with self.subTest(period=period):
                self.assertEqual(
                    str(regular_deadline(date.fromisoformat(period))), expected
                )

    def test_income_paid_by_reconciled_setoff_uses_the_actual_tax_result(self):
        notice = self.notice()
        notice.event_ids[0].payment_line_id.move_id._reverse_moves(cancel=True)
        receivable = self.company_data["default_account_receivable"]
        claim = self.entry(
            "Actual mutual receivable",
            [(receivable, 19800), (self.profit, -19800)],
            "2026-05-19",
        )
        offset = self.entry(
            "Reviewed set-off agreement",
            [(self.dividend, 19800), (receivable, -19800)],
            "2026-05-20",
        )
        line = offset.line_ids.filtered(lambda row: row.account_id == self.dividend)
        notice.event_ids.write(
            {
                "payment_line_id": line.id,
                "payment_form": "setoff",
                "source_reference": "Synthetic actual set-off agreement and mutual claim",
                "payment_reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "reconciled mutual receivable"):
            notice.action_compute_lines()
        (claim | offset).line_ids.filtered(
            lambda row: row.account_id == receivable
        ).reconcile()
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()
        self.assertEqual(
            etree.fromstring(notice.submitted_attachment_id.raw).findtext(
                "hlavicka/suhrnneUdaje/spolu04/danZrazena"
            ),
            "1700.00",
        )
        self.assertTrue(
            all(
                source["payment_form"] == "setoff"
                for source in notice.payload["sources"]
            )
        )

    def test_registered_native_payments_through_outstanding_account(self):
        notice = self.notice()
        notice.event_ids[0].payment_line_id.move_id._reverse_moves(cancel=True)
        notice.event_ids[0].remittance_ids.line_id.move_id._reverse_moves(cancel=True)
        journal = self.company_data["default_journal_bank"]
        outstanding = self.env["account.account"].create(
            {
                "code": "261987",
                "name": "Synthetic outstanding payments",
                "account_type": "asset_current",
                "reconcile": True,
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        method = journal.outbound_payment_method_line_ids[:1]
        self.assertTrue(method)
        method.payment_account_id = outstanding

        def registered(amount, account, actual_on):
            payment = self.env["account.payment"].create(
                {
                    "company_id": self.company.id,
                    "journal_id": journal.id,
                    "payment_type": "outbound",
                    "partner_type": "supplier",
                    "partner_id": self.recipient.id,
                    "destination_account_id": account.id,
                    "payment_method_line_id": method.id,
                    "amount": amount,
                    "date": actual_on,
                }
            )
            payment.action_post()
            self.assertEqual(payment.move_id.state, "posted")
            self.assertFalse(
                payment.move_id.line_ids.filtered(
                    lambda row: row.account_id.account_type == "asset_cash"
                )
            )
            self.assertEqual(payment.move_id.origin_payment_id, payment)
            return payment.move_id.line_ids.filtered(
                lambda row: row.account_id == account
            )

        payout = registered(19800, self.dividend, "2026-05-20")
        remitted = registered(1700, self.tax, "2026-06-15")
        notice.event_ids.write(
            {
                "payment_line_id": payout.id,
                "payment_reviewed": True,
                "source_reference": "Synthetic bank acceptance evidence for actual registered disbursement",
            }
        )
        notice.event_ids.remittance_ids.write(
            {"line_id": remitted.id, "reviewed": True}
        )
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()
        self.assertEqual(
            etree.fromstring(notice.submitted_attachment_id.raw).findtext(
                "hlavicka/suhrnneUdaje/spolu04/danOdvedena"
            ),
            "1700.00",
        )

    def test_arbitrary_current_asset_credit_is_not_a_registered_payment(self):
        notice = self.notice()
        account = self.env["account.account"].create(
            {
                "code": "261988",
                "name": "Unproven transit",
                "account_type": "asset_current",
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        move = self.entry(
            "Not a registered payment",
            [(self.dividend, 19800), (account, -19800)],
            "2026-05-20",
        )
        notice.event_ids.write(
            {
                "payment_line_id": move.line_ids.filtered(
                    lambda row: row.account_id == self.dividend
                ).id,
                "payment_reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "native registered outbound payment"):
            notice.action_compute_lines()

    def test_combined_gross_liability_withholding_and_net_payment(self):
        for form in ("disbursement", "setoff"):
            with self.subTest(form=form):
                notice = self.notice()
                notice.event_ids[0].payment_line_id.move_id._reverse_moves(cancel=True)
                notice.event_ids[0].withholding_line_id.move_id._reverse_moves(
                    cancel=True
                )
                target = (
                    self.bank
                    if form == "disbursement"
                    else self.company_data["default_account_receivable"]
                )
                move = self.entry(
                    "Combined gross settlement and withholding",
                    [(self.dividend, 21500), (self.tax, -1700), (target, -19800)],
                    "2026-05-20",
                )
                if form == "setoff":
                    claim = self.entry(
                        "Actual mutual claim",
                        [(target, 19800), (self.profit, -19800)],
                        "2026-05-19",
                    )
                    (claim | move).line_ids.filtered(
                        lambda row: row.account_id == target
                    ).reconcile()
                notice.event_ids.write(
                    {
                        "payment_line_id": move.line_ids.filtered(
                            lambda row: row.account_id == self.dividend
                        ).id,
                        "withholding_line_id": move.line_ids.filtered(
                            lambda row: row.account_id == self.tax
                        ).id,
                        "payment_form": form,
                        "payment_reviewed": True,
                    }
                )
                notice.action_compute_lines()
                notice.action_export_xml()
                self.assertEqual(
                    etree.fromstring(notice.xml_attachment_id.raw).findtext(
                        "hlavicka/suhrnneUdaje/spolu04/danZrazena"
                    ),
                    "1700.00",
                )

    def test_small_cash_credit_cannot_prove_a_large_reported_payment(self):
        notice = self.notice()
        account = self.env["account.account"].create(
            {
                "code": "261989",
                "name": "Unsettled transit",
                "account_type": "asset_current",
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        move = self.entry(
            "Only part of debit actually paid",
            [(self.dividend, 19800), (self.bank, -1), (account, -19799)],
            "2026-05-20",
        )
        notice.event_ids.write(
            {
                "payment_line_id": move.line_ids.filtered(
                    lambda row: row.account_id == self.dividend
                ).id,
                "payment_reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "actual settlement credits"):
            notice.action_compute_lines()

    def test_changing_payment_form_keeps_actual_payment_date(self):
        notice = self.notice()
        event = notice.event_ids[0]
        event.paid_on = "2026-05-19"
        event.payment_form = "setoff"
        event._onchange_payment_form()
        self.assertEqual(event.paid_on, date(2026, 5, 19))
        self.assertFalse(event.payment_reviewed)

    def test_same_cash_credits_cannot_back_distinct_counterpart_lines_twice(self):
        first = self.notice()
        account = self.env["account.account"].create(
            {
                "code": "261991",
                "name": "Unsettled second debit",
                "account_type": "asset_current",
                "company_ids": [Command.set(self.company.ids)],
            }
        )
        move = self.entry(
            "Shared bank credits, distinct liabilities",
            [
                (self.dividend, 19800),
                (self.dividend, 1000),
                (self.bank, -19800),
                (account, -1000),
            ],
            "2026-05-20",
        )
        first.event_ids.write(
            {
                "payment_line_id": move.line_ids.filtered(
                    lambda row: row.account_id == self.dividend and row.balance == 19800
                ).id,
                "payment_reviewed": True,
            }
        )
        first.action_compute_lines()
        second = self.notice()
        second.write(
            {
                "period": "2026-06-01",
                "prepared_on": "2026-07-15",
                "filing_on": "2026-07-15",
            }
        )
        second.event_ids[0].unlink()
        second.event_ids.write(
            {
                "gross": 1000,
                "paid_on": "2026-06-20",
                "payment_line_id": move.line_ids.filtered(
                    lambda row: row.account_id == self.dividend and row.balance == 1000
                ).id,
                "payment_reviewed": True,
            }
        )
        second.event_ids.remittance_ids.write(
            {"amount": 70, "actual_on": "2026-07-15", "reviewed": True}
        )
        with self.assertRaisesRegex(UserError, "actual settlement credits"):
            second.action_compute_lines()

    def test_source_and_income_chronology_guards_have_valid_baselines(self):
        cases = {
            "unposted": "posted source lines",
            "wrong_sign": "posted source lines",
            "wrong_dividend": "dividend 364",
            "wrong_author": "supplier or other payable",
            "unfinished_profit": "completed profit period",
            "late_decision": "actual payment dates",
            "zero_withholding": "zero-tax dividend",
        }
        for case, message in cases.items():
            with self.subTest(case=case):
                notice = self.notice()
                notice.action_compute_lines()
                notice.action_reset_to_draft()
                event = notice.event_ids[0]
                values = {"payment_reviewed": True}
                if case == "unposted":
                    event.payment_line_id.move_id.button_draft()
                elif case == "wrong_sign":
                    values["payment_line_id"] = event.distribution_line_id.id
                elif case == "wrong_dividend":
                    values["distribution_line_id"] = event.withholding_line_id.id
                elif case == "wrong_author":
                    values["income_kind"] = "author"
                elif case == "unfinished_profit":
                    values["profit_period_end"] = "2026-05-11"
                elif case == "late_decision":
                    values["decision_on"] = "2026-05-21"
                elif case == "zero_withholding":
                    values["gross"] = 0.01
                event.write(values)
                with self.assertRaisesRegex(UserError, message):
                    notice.action_compute_lines()

    def test_native_sources_are_reserved_across_live_notices(self):
        first = self.notice()
        first.action_compute_lines()
        second = self.notice()
        second.write(
            {
                "period": "2026-06-01",
                "prepared_on": "2026-07-15",
                "filing_on": "2026-07-15",
            }
        )
        second.event_ids[0].unlink()
        event = second.event_ids
        event.write({"gross": 1000, "paid_on": "2026-06-20", "payment_reviewed": True})
        event.remittance_ids.write(
            {"amount": 70, "actual_on": "2026-07-15", "reviewed": True}
        )
        own = event.remittance_ids.line_id
        event.remittance_ids.write(
            {"line_id": first.event_ids[0].remittance_ids.line_id.id, "reviewed": True}
        )
        with self.assertRaisesRegex(UserError, "another live notice"):
            second.action_compute_lines()
        event.remittance_ids.write({"line_id": own.id, "reviewed": True})
        for field in ("distribution_line_id", "payment_line_id", "withholding_line_id"):
            original = event[field]
            event.write({field: first.event_ids[0][field].id, "payment_reviewed": True})
            with self.assertRaisesRegex(UserError, "another live notice"):
                second.action_compute_lines()
            event.write({field: original.id, "payment_reviewed": True})
        second.action_compute_lines()
        self.assertEqual(second.state, "preview")
        first.action_export_xml()
        first.action_submit()
        second.action_reset_to_draft()
        event.remittance_ids.write(
            {"line_id": first.event_ids[0].remittance_ids.line_id.id, "reviewed": True}
        )
        with self.assertRaisesRegex(UserError, "another live notice"):
            second.action_compute_lines()
        amendment = self.env[MODEL].browse(first.action_create_amendment()["res_id"])
        amendment.event_ids.unlink()
        # An unfinished correction cannot release the still-filed allocation.
        self.assertEqual(
            second._allocated_elsewhere()[first.event_ids[0].remittance_ids.line_id.id],
            1700,
        )

    def test_actual_filing_retains_export_after_recipient_address_change(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content = notice.xml_attachment_id.raw
        self.recipient.street = "Changed after actual export"
        action = notice.action_create_submission(channel="pfs_manual")
        submission = self.env["cssk.submission"].browse(action["res_id"])
        submission.action_attest_manual()
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(submission.state, "delivered")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(len(notice.source_history), 1)

    def test_actual_filing_survives_renderer_upgrade_and_binary_size_context(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content, payload = notice.xml_attachment_id.raw, deepcopy(notice.payload)
        with patch.object(wire4311, "render", side_effect=ValueError("New schema")):
            action = notice.with_context(bin_size=True).action_create_submission(
                channel="pfs_manual"
            )
            submission = self.env["cssk.submission"].browse(action["res_id"])
            submission.with_context(bin_size=True).action_attest_manual()
        self.assertEqual(submission.state, "delivered")
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(notice.source_history[-1]["payload"], payload)

    def test_filing_drift_check_does_not_swallow_access_error(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        with patch.object(type(notice), "_sources", side_effect=AccessError("Denied")):
            with self.assertRaises(AccessError):
                notice.action_submit()
        self.assertEqual(notice.state, "exported")
        self.assertFalse(notice.filed_history_ids)

    def later_conflicting_draft(self, first):
        later = self.notice()
        later.write(
            {
                "period": "2026-06-01",
                "prepared_on": "2026-07-15",
                "filing_on": "2026-07-15",
            }
        )
        for source, draft in zip(first.event_ids, later.event_ids):
            draft.write(
                {
                    "distribution_line_id": source.distribution_line_id.id,
                    "payment_line_id": source.payment_line_id.id,
                    "withholding_line_id": source.withholding_line_id.id,
                    "paid_on": "2026-06-20",
                }
            )
        self.assertEqual(later.state, "draft")
        self.assertTrue(later._reserved_lines())
        self.assertFalse(later._reserved_lines(retained_only=True))
        return later

    def test_later_draft_does_not_preempt_recording_the_retained_filing(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content, payload = notice.xml_attachment_id.raw, deepcopy(notice.payload)
        self.assertTrue(notice._reserved_lines(retained_only=True))
        later = self.later_conflicting_draft(notice)
        notice.action_submit()
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(notice.source_history[-1]["payload"], payload)
        self.assertEqual(later.state, "draft")
        with self.assertRaises(UserError):
            later.action_compute_lines()

    def test_later_draft_cannot_leave_manual_delivery_exported(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content, payload = notice.xml_attachment_id.raw, deepcopy(notice.payload)
        later = self.later_conflicting_draft(notice)
        action = notice.with_context(bin_size=True).action_create_submission(
            channel="pfs_manual"
        )
        submission = self.env["cssk.submission"].browse(action["res_id"])
        submission.with_context(bin_size=True).action_attest_manual()
        self.assertEqual(submission.state, "delivered")
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(notice.source_history[-1]["payload"], payload)
        self.assertEqual(later.state, "draft")

    def test_filing_refuses_corrupted_retained_attachment_checksum(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_export_xml()
        attachment = notice.xml_attachment_id
        self.env.cr.execute(
            "UPDATE ir_attachment SET checksum = %s WHERE id = %s",
            ["0" * 40, attachment.id],
        )
        attachment.invalidate_recordset(["checksum", "raw"])
        with self.assertRaisesRegex(UserError, "exported attachment"):
            notice.action_submit()
        self.assertEqual(notice.state, "exported")
        self.assertFalse(notice.filed_history_ids)

    def test_posting_is_not_payment_and_unpaid_tax_is_not_fictitiously_remitted(self):
        notice = self.notice(paid=False, remitted=False)
        with self.assertRaises(UserError):
            notice.action_compute_lines()
        notice.event_ids.payment_reviewed = True
        notice.action_compute_lines()
        notice.action_export_xml()
        xml = etree.fromstring(base64.b64decode(notice.xml_attachment_id.datas))
        self.assertEqual(
            xml.findtext("hlavicka/suhrnneUdaje/spolu04/danOdvedena"), "0.00"
        )

    def test_other_person_sources_and_overallocated_native_lines_are_rejected(self):
        notice = self.notice()
        notice.event_ids[0].write(
            {
                "partner_id": self.env["res.partner"]
                .create({"name": "Another synthetic person"})
                .id,
                "payment_reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "counterparty"):
            notice.action_compute_lines()
        notice.event_ids[0].write(
            {"partner_id": self.recipient.id, "payment_reviewed": True}
        )
        notice.event_ids[1].write({"gross": 15001, "payment_reviewed": True})
        with self.assertRaisesRegex(UserError, "exceed"):
            notice.action_compute_lines()

    def test_actual_income_date_is_independent_of_month_end_tax_booking(self):
        notice = self.notice(withholding_day="2026-05-31").with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        xml = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(
            xml.findtext("telo/prilohaA/udajeA_1/udajeOZrazeniAOdvedeni/datumUhrady"),
            "20.05.2026",
        )
        notice.action_reset_to_draft()
        notice.event_ids[0].paid_on = "2026-05-21"
        self.assertFalse(notice.event_ids[0].payment_reviewed)

    def test_correction_and_storage_migration_preserve_exact_original(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()
        attachment, payload = notice.submitted_attachment_id, deepcopy(notice.payload)
        content = attachment.raw
        action = notice.action_create_amendment()
        correction = self.env[MODEL].browse(action["res_id"])
        with self.assertRaisesRegex(UserError, "filing receipt"):
            correction.action_compute_lines()
        correction.write(
            {
                "original_filing_date": "2026-06-16",
                "correction_source_reference": "Synthetic FS receipt dated June16",
                "original_date_reviewed": True,
            }
        )
        correction.action_compute_lines()
        correction.action_export_xml()
        self.assertEqual(
            etree.fromstring(correction.xml_attachment_id.raw).findtext(
                "hlavicka/datumPovodne"
            ),
            "16.06.2026",
        )
        self.assertEqual(
            etree.fromstring(correction.xml_attachment_id.raw).findtext(
                "hlavicka/dovodDoplnenia"
            ),
            "1",
        )
        attachment.write({"raw": content})
        attachment._migrate()
        with self.assertRaises(UserError):
            attachment.write({"raw": b"tampered"})
        self.assertEqual(attachment.raw, content)
        self.assertEqual(notice.payload, payload)

    def test_sources_and_generated_evidence_cannot_be_changed_behind_export(self):
        notice = self.notice()
        for values in (
            {"state": "submitted"},
            {"payload": {}},
            {"xml_attachment_id": False},
        ):
            with self.assertRaises(UserError):
                notice.write(values)
        with self.assertRaises(UserError):
            self.env[MODEL].with_context(default_state="submitted").create({})
        notice.action_compute_lines()
        notice.action_export_xml()
        with self.assertRaises(UserError):
            notice.event_ids[0].gross = 1
        self.company.street = "Changed source3"
        content = notice.xml_attachment_id.raw
        notice.action_submit()
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)

    def test_filed_identity_survives_manager_reset_and_empty_working_rows(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()
        notice.action_reset_to_draft()
        notice.write({"period": notice.period})
        other = self.env["res.company"].create({"name": "Other synthetic4311 owner"})
        for values in (
            {"event_ids": [Command.clear()], "company_id": other.id},
            {"period": "2026-06-01"},
            {"original_return_id": notice.id},
        ):
            with self.subTest(values=values), self.assertRaises(UserError):
                notice.write(values)
        self.assertEqual(notice.company_id, self.company)
        self.assertEqual(len(notice.event_ids), 2)

    def test_preparation_date_does_not_exclude_payment_before_actual_filing(self):
        notice = self.notice()
        notice.prepared_on = "2026-06-14"
        notice.action_compute_lines()
        self.assertEqual(sum(row["remitted"] for row in notice.payload["events"]), 1700)
        notice.action_export_xml()
        root = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(
            root.findtext("hlavicka/suhrnneUdaje/spolu04/danOdvedena"), "1700.00"
        )

    def test_partial_multiple_and_future_remittances_keep_individual_evidence(self):
        notice = self.notice(remitted=False)
        event = notice.event_ids[0]
        for amount, day in (
            (200, "2026-06-10"),
            (450, "2026-06-15"),
            (1, "2026-06-20"),
        ):
            move = self.entry(
                "partial tax transfer", [(self.tax, amount), (self.bank, -amount)], day
            )
            self.env["l10n.sk.withholding.remittance"].create(
                {
                    "event_id": event.id,
                    "line_id": move.line_ids.filtered(
                        lambda row: row.account_id == self.tax
                    ).id,
                    "amount": amount,
                    "actual_on": day,
                    "reviewed": True,
                    "source_reference": "Synthetic bank payment " + day,
                }
            )
        self.assertEqual(event.remitted, 650)
        with self.assertRaisesRegex(UserError, "one remittance date"):
            notice.action_compute_lines()
        event.write(
            {
                "reported_remitted_on": "2026-06-15",
                "remittance_reporting_reviewed": True,
            }
        )
        notice.action_compute_lines()
        self.assertEqual(notice.payload["events"][0]["remitted"], 650)
        self.assertEqual(len(notice.payload["sources"][0]["remittances"]), 2)
        notice.action_export_xml()
        with self.assertRaises(UserError):
            event.remittance_ids[0].amount = 201
        notice.action_reset_to_draft()
        event.remittance_ids[0].source_reference = "Changed payment proof"
        self.assertFalse(event.remittance_ids[0].reviewed)
        self.assertFalse(event.remittance_reporting_reviewed)
        event.remittance_ids[0].reviewed = True
        notice.filing_on = "2026-06-20"
        self.assertEqual(event.remitted, 651)
        event.write(
            {
                "reported_remitted_on": "2026-06-20",
                "remittance_reporting_reviewed": True,
            }
        )
        # A later excess payment cannot be allocated to an income whose tax is650.
        with self.assertRaises(UserError):
            notice.action_compute_lines()

    def test_author_partial_credit_note_uses_remaining_native_income(self):
        notice = self.notice(remitted=False)
        notice.event_ids.unlink()
        payable = self.recipient.with_company(self.company).property_account_payable_id
        self.assertTrue(payable.code.startswith("321"))
        purchase = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")], limit=1
        )
        bill = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": purchase.id,
                "partner_id": self.recipient.id,
                "move_type": "in_invoice",
                "invoice_date": "2026-05-10",
                "date": "2026-05-10",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Synthetic author licence",
                            "account_id": self.expense.id,
                            "quantity": 1,
                            "price_unit": 1500,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        bill.action_post()
        credit = bill._reverse_moves(
            default_values_list=[
                {
                    "date": "2026-05-15",
                    "invoice_date": "2026-05-15",
                }
            ]
        )
        self.assertEqual(credit.state, "draft")
        credit.invoice_line_ids.price_unit = 150
        credit.action_post()
        self.assertEqual(credit.reversed_entry_id, bill)
        self.assertEqual(credit.amount_total, 150)
        income = bill.line_ids.filtered(lambda line: line.account_id == payable)
        self.assertEqual(len(income), 1)
        self.assertEqual(income.balance, -1500)
        tax = self.entry(
            "remaining author tax", [(payable, 256.5), (self.tax, -256.5)], "2026-05-20"
        )
        payment = self.entry(
            "remaining author payment",
            [(payable, 1093.5), (self.bank, -1093.5)],
            "2026-05-20",
        )
        event = self.env["l10n.sk.withholding.event"].create(
            {
                "notice_id": notice.id,
                "partner_id": self.recipient.id,
                "first_name": "Žofia",
                "last_name": "Šťastná",
                "income_kind": "author",
                "gross": 1350,
                "decision_on": "2026-05-10",
                "paid_on": "2026-05-20",
                "distribution_line_id": income.id,
                "withholding_line_id": tax.line_ids.filtered(
                    lambda line: line.account_id == self.tax
                ).id,
                "payment_line_id": payment.line_ids.filtered(
                    lambda line: line.account_id == payable
                ).id,
                "source_reference": "Synthetic licence, native bill/partial credit and actual payment",
                "payment_reviewed": True,
            }
        )
        self.assertEqual(event.tax_amount, 256.5)
        self.assertEqual(event.net_amount, 1093.5)
        try:
            notice.action_compute_lines()
        except UserError as error:
            self.fail(f"Remaining native author income could not be reported: {error}")
        notice.action_export_xml()
        root = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(
            root.findtext("hlavicka/suhrnneUdaje/spolu04/danZrazena"), "256.50"
        )
        etree.XMLSchema(
            etree.parse(file_path("l10n_sk_withholding/data/ozn4311_2026.xsd"))
        ).assertValid(root)

    def test_resident_author_without_waiver_uses_19_percent_not_dividend_annex(self):
        notice = self.notice(remitted=False)
        notice.event_ids.unlink()
        liability = self.entry(
            "author licence payable",
            [(self.expense, 1500), (self.author_payable, -1500)],
            "2026-05-10",
        )
        tax = self.entry(
            "author tax withheld",
            [(self.author_payable, 285), (self.tax, -285)],
            "2026-05-31",
        )
        payment = self.entry(
            "author net licence payment",
            [(self.author_payable, 1215), (self.bank, -1215)],
            "2026-05-20",
        )
        event = self.env["l10n.sk.withholding.event"].create(
            {
                "notice_id": notice.id,
                "partner_id": self.recipient.id,
                "first_name": "Žofia",
                "last_name": "Šťastná",
                "income_kind": "author",
                "gross": 1500,
                "decision_on": "2026-05-10",
                "paid_on": "2026-05-20",
                "distribution_line_id": liability.line_ids.filtered(
                    lambda row: row.account_id == self.author_payable
                ).id,
                "withholding_line_id": tax.line_ids.filtered(
                    lambda row: row.account_id == self.tax
                ).id,
                "payment_line_id": payment.line_ids.filtered(
                    lambda row: row.account_id == self.author_payable
                ).id,
                "source_reference": "Synthetic signed licence and actual bank payment",
                "payment_reviewed": True,
            }
        )
        self.assertEqual(event.tax_amount, 285)
        self.assertEqual(event.net_amount, 1215)
        notice.action_compute_lines()
        notice.action_export_xml()
        root = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(
            root.findtext("hlavicka/suhrnneUdaje/spolu04/danZrazena"), "285.00"
        )
        self.assertIsNone(root.find("telo/prilohaA"))
        notice.action_reset_to_draft()
        event.write({"no_withholding_agreement": True, "payment_reviewed": True})
        self.assertEqual(event.tax_amount, 0)
        with self.assertRaisesRegex(UserError, "43\\(14\\)"):
            notice.action_compute_lines()

    def test_derived_amounts_cannot_be_injected_through_api_or_defaults(self):
        notice = self.notice()
        event = notice.event_ids[0]
        for key in ("remitted", "tax_amount", "net_amount", "company_id"):
            with self.subTest(key=key), self.assertRaises(UserError):
                event.write({key: 1})
            with self.subTest(default=key), self.assertRaises(UserError):
                self.env[event._name].with_context(**{"default_" + key: 1}).create({})

    def test_filed_original_cannot_be_rewritten_as_another_original(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()
        original = notice.submitted_attachment_id.raw
        notice.action_reset_to_draft()
        notice.prepared_by = "Different printed preparer"
        notice.action_compute_lines()
        with self.assertRaisesRegex(UserError, "explicit correction"):
            notice.action_export_xml()
        self.assertEqual(notice.submitted_attachment_id.raw, original)

    def test_schema_pin_matches_bundled_bytes_and_no_schema_is_unpinned(self):
        root = Path(file_path("l10n_sk_withholding"))
        pin = (root / "data/SCHEMA_VERSION").read_text()
        entries = re.findall(r"^(\S+\.xsd)\s+([a-f0-9]{32})\s+(\d+)$", pin, re.M)
        self.assertTrue(entries)
        self.assertEqual(
            {name for name, _, _ in entries},
            {path.name for path in (root / "data").glob("*.xsd")},
        )
        for name, digest, size in entries:
            content = (root / "data" / name).read_bytes()
            self.assertEqual(hashlib.md5(content).hexdigest(), digest)
            self.assertEqual(len(content), int(size))

    def test_second_correction_uses_the_immediately_previous_filed_notice(self):
        original = self.notice()
        original.action_compute_lines()
        original.action_export_xml()
        original.action_submit()
        first = self.env[MODEL].browse(original.action_create_amendment()["res_id"])
        first.write(
            {
                "prepared_on": "2026-06-20",
                "filing_on": "2026-06-20",
                "original_filing_date": "2026-06-15",
                "original_date_reviewed": True,
                "correction_source_reference": "Synthetic first filing receipt",
            }
        )
        first.action_compute_lines()
        first.action_export_xml()
        first.action_submit()
        second = self.env[MODEL].browse(original.action_create_amendment()["res_id"])
        self.assertEqual(second.original_return_id, first)
        self.assertFalse(second.original_date_reviewed)
        second.write(
            {
                "original_return_id": original.id,
                "original_filing_date": "2026-06-15",
                "original_date_reviewed": True,
                "correction_source_reference": "Synthetic obsolete receipt",
            }
        )
        with self.assertRaisesRegex(UserError, "immediately previous"):
            second.action_compute_lines()

    def test_actual_authority_allocation_is_distinct_from_a_bank_transfer(self):
        notice = self.notice()
        row = notice.event_ids[0].remittance_ids
        settlement = self.entry(
            "actual authority settlement",
            [(self.tax, 650), (self.author_payable, -650)],
            "2026-06-15",
        )
        row.write(
            {
                "line_id": settlement.line_ids.filtered(
                    lambda line: line.account_id == self.tax
                ).id,
                "reviewed": True,
                "source_reference": "Synthetic actual authority settlement decision",
            }
        )
        with self.assertRaisesRegex(UserError, "bank or cash"):
            notice.action_compute_lines()
        row.write({"source_kind": "authority", "reviewed": True})
        notice.action_compute_lines()
        self.assertEqual(notice.payload["events"][0]["remitted"], 650)
        self.assertEqual(
            notice.payload["sources"][0]["remittances"][0]["source_kind"], "authority"
        )
