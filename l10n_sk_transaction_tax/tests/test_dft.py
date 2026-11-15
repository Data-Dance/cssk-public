# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy
from datetime import date
from unittest.mock import patch
from lxml import etree
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from ..deadlines import monthly_deadline
from .. import wire

MODEL = "l10n.sk.transaction.tax"


@tagged("post_install", "-at_install")
class TestDftNative(AccountTestInvoicingCommon):
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
                "vat": False,
                "street": "Testovacia1",
                "city": "Bratislava",
                "zip": "85110",
            }
        )
        cls.general = cls.company_data["default_journal_misc"]
        cls.bank = cls.company_data["default_journal_bank"].default_account_id

        def account(code, kind):
            return cls.env["account.account"].create(
                {
                    "code": code,
                    "name": "Synthetic DFT " + code,
                    "account_type": kind,
                    "company_ids": [Command.set(cls.company.ids)],
                }
            )

        cls.payable = account("321987", "liability_current")
        cls.expense = account("538987", "expense")
        cls.tax = account("345987", "liability_current")
        cls.cash = account("211987", "asset_cash")
        cls.representative = cls.env["res.partner"].create(
            {"name": "Syntetická Osoba", "country_id": cls.env.ref("base.sk").id}
        )
        cls.operator = cls.env["res.users"].create(
            {
                "name": "Synthetic DFT accountant",
                "login": "synthetic-dft-accountant",
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

    def entry(self, amount, debit=None, credit=None, date="2026-05-20", journal=None):
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": (
                    journal or self.company_data["default_journal_bank"]
                    if (credit or self.bank) == self.bank
                    else journal or self.general
                ).id,
                "date": date,
                "ref": "SYNTHETIC DFT SOURCE",
                "line_ids": [
                    Command.create(
                        {
                            "name": "Synthetic debit",
                            "account_id": (debit or self.payable).id,
                            "debit": amount,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Synthetic credit",
                            "account_id": (credit or self.bank).id,
                            "credit": amount,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def notice(self, amount=30000, kind="transfer", **values):
        actual = str(
            self.env[MODEL]
            ._fields["period"]
            .to_date(values.get("period", "2026-05-01"))
            .replace(day=20)
        )
        move = self.entry(
            amount, debit=self.cash if kind == "cash" else None, date=actual
        )
        recharged = kind.startswith("recharge_")
        result = {
            "company_id": self.company.id,
            "period": "2026-05-01",
            "signed_on": "2026-06-30",
            "filing_on": "2026-06-30",
            "deadline": "2026-06-30",
            "deadline_reference": "Synthetic reviewed statutory calendar",
            "grounds_c": not recharged,
            "grounds_d": recharged,
            "representative_kind": "statutarnyZastupcaPO",
            "representative_id": self.representative.id,
            "representative_first_name": "Syntetická",
            "representative_last_name": "Osoba",
            "provision_journal_id": self.general.id,
            "provision_expense_account_id": self.expense.id,
            "provision_payable_account_id": self.tax.id,
            "source_ids": [
                Command.create(
                    {
                        "move_line_id": move.line_ids.filtered(
                            lambda line: line.account_id
                            == (self.payable if recharged else self.bank)
                        ).id,
                        "kind": kind,
                        "transaction_reference": "Synthetic-original-T1"
                        if recharged
                        else False,
                        "actual_on": actual,
                        "source_reference": "Synthetic foreign bank statement and payer evidence",
                        "reviewed": True,
                    }
                )
            ],
        }
        result.update(values)
        return self.env[MODEL].create(result)

    def file(self, notice):
        notice.action_compute_lines()
        notice.action_export_xml()
        notice.action_submit()

    def test_reversed_sources_and_reversal_lines_are_not_taxable_payments(self):
        notice = self.notice()
        source = notice.source_ids.move_line_id.move_id
        reverse = source._reverse_moves(cancel=True)
        with self.assertRaisesRegex(UserError, "unreversed"):
            notice.action_compute_lines()
        notice.source_ids.move_line_id = reverse.line_ids.filtered(
            lambda line: line.account_id == self.bank
        )
        with self.assertRaisesRegex(UserError, "unreversed"):
            notice.action_compute_lines()

    def test_reviewed_bank_batch_has_one_cap_per_payment(self):
        notice = self.notice(50000)
        first = notice.source_ids
        first.write(
            {
                "bank_batch": True,
                "source_amount": "5000",
                "transaction_reference": "payment-0",
                "reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "whole native bank line"):
            notice.action_compute_lines()
        for index in range(1, 10):
            first.copy({"transaction_reference": "payment-%s" % index})
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 200)
        self.assertEqual(
            len({row["transaction_key"] for row in notice.payload["rows"]}), 10
        )
        notice.action_post_provision()
        notice.action_export_xml()
        notice.action_submit()
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.expense
            ).balance,
            200,
        )
        other = self.notice(
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        other.source_ids.unlink()
        for source in notice.source_ids:
            source.copy({"notice_id": other.id, "actual_on": "2026-06-20"})
        with self.assertRaisesRegex(UserError, "already allocated"):
            other.action_compute_lines()

    def test_bank_batch_minimum_and_duplicate_references(self):
        notice = self.notice(0.02)
        first = notice.source_ids
        first.write(
            {
                "bank_batch": True,
                "source_amount": "0.01",
                "transaction_reference": "micro-1",
                "reviewed": True,
            }
        )
        second = first.copy({"transaction_reference": "micro-1"})
        with self.assertRaisesRegex(UserError, "duplicate"):
            notice.action_compute_lines()
        second.write({"transaction_reference": "micro-2", "reviewed": True})
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 0.02)

    def test_monthly_deadline_cannot_be_arbitrarily_extended(self):
        notice = self.notice(deadline="2099-12-31")
        self.assertEqual(notice.deadline, date(2026, 6, 30))
        notice.write(
            {
                "signed_on": "2026-09-15",
                "filing_on": "2026-09-15",
            }
        )
        self.file(notice)
        self.assertTrue(
            any(
                "after its statutory deadline" in str(message.body)
                for message in notice.message_ids
            )
        )
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 11, 10)):
            correction = self.env[MODEL].browse(
                notice.action_create_amendment()["res_id"]
            )
        self.assertEqual(correction.filing_type, "additional")
        self.assertEqual(correction.discovery_date, date(2026, 11, 10))

    def test_monthly_deadlines_weekends_holidays_and_december_cards(self):
        for period, expected in [
            ("2026-01-01", "2026-03-02"),
            ("2026-04-01", "2026-06-01"),
            ("2026-09-01", "2026-11-02"),
            ("2026-12-01", "2027-02-01"),
            ("2027-01-01", "2027-03-01"),
            ("2027-02-01", "2027-03-31"),
        ]:
            with self.subTest(period=period):
                self.assertEqual(
                    str(monthly_deadline(date.fromisoformat(period))), expected
                )

    def test_frozen_export_allocations_are_rechecked_when_filed(self):
        first = self.notice(1000)
        first.action_compute_lines()
        first.action_export_xml()
        later = self.notice(
            1000,
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        later.source_ids.write(
            {"move_line_id": first.source_ids.move_line_id.id, "reviewed": True}
        )
        later.action_compute_lines()
        later.action_export_xml()
        first.action_submit()
        with self.assertRaisesRegex(UserError, "already allocated"):
            later.action_submit()
        self.assertEqual(later.state, "exported")
        self.assertFalse(later.filed_history_ids)

    def test_filed_liability_uses_retained_payload_after_source_reversal(self):
        notice = self.notice().with_user(self.operator)
        self.file(notice)
        content = notice.submitted_attachment_id.raw
        notice.source_ids.move_line_id.move_id.sudo()._reverse_moves(cancel=True)
        notice.action_post_provision()
        self.assertEqual(notice.tax_total, 40)
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertTrue(
            any(
                "Current DFT sources differ" in str(message.body)
                for message in notice.message_ids
            )
        )

    def test_filing_and_filed_liability_survive_renderer_upgrade(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content, payload = notice.xml_attachment_id.raw, deepcopy(notice.payload)
        with patch.object(wire, "render", side_effect=ValueError("New schema")):
            action = notice.with_context(bin_size=True).action_create_submission(
                channel="pfs_manual"
            )
            submission = self.env["cssk.submission"].browse(action["res_id"])
            submission.with_context(bin_size=True).action_attest_manual()
            notice.with_context(bin_size=True).action_post_provision()
        self.assertEqual(submission.state, "delivered")
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(notice.source_history[-1]["payload"], payload)
        self.assertEqual(notice.tax_total, 40)
        self.assertEqual(notice.provision_move_id.state, "posted")

    def test_filing_drift_check_does_not_swallow_access_error(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        with patch.object(type(notice), "_sources", side_effect=AccessError("Denied")):
            with self.assertRaises(AccessError):
                notice.action_submit()
        self.assertEqual(notice.state, "exported")
        self.assertFalse(notice.filed_history_ids)

    def test_posting_needs_computed_amount_and_correct_accounts(self):
        notice = self.notice()
        with self.assertRaisesRegex(UserError, "Compute"):
            notice.action_post_provision()
        notice.action_compute_lines()
        notice.action_reset_to_draft()
        notice.provision_expense_account_id = self.payable
        notice.action_compute_lines()
        with self.assertRaisesRegex(UserError, "538/345"):
            notice.action_post_provision()
        notice.action_reset_to_draft()
        notice.write(
            {
                "provision_expense_account_id": self.expense.id,
                "provision_journal_id": self.company_data["default_journal_bank"].id,
            }
        )
        notice.action_compute_lines()
        with self.assertRaisesRegex(UserError, "general journal"):
            notice.action_post_provision()

    def test_source_guards_unposted_wrong_side_missing_reference_and_fractional_units(
        self,
    ):
        notice = self.notice()
        source = notice.source_ids
        move = source.move_line_id.move_id
        move.button_draft()
        with self.assertRaisesRegex(UserError, "posted native"):
            notice.action_compute_lines()
        move.action_post()
        source.write(
            {
                "move_line_id": move.line_ids.filtered(
                    lambda line: line.account_id == self.payable
                ).id,
                "reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "payment account"):
            notice.action_compute_lines()
        recharge = self.notice(1000, "recharge_known")
        recharge.source_ids.write({"transaction_reference": False, "reviewed": True})
        with self.assertRaisesRegex(UserError, "third-party"):
            recharge.action_compute_lines()
        recharge.source_ids.write(
            {
                "transaction_reference": "actual-original",
                "source_amount": "0.001",
                "reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "whole monetary units"):
            recharge.action_compute_lines()

    def test_filing_requires_own_export_attachment_matching_retained_payload(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_export_xml()
        foreign = self.env["ir.attachment"].create(
            {
                "name": "Different owner",
                "raw": notice.xml_attachment_id.raw,
                "res_model": MODEL,
                "res_id": 0,
            }
        )
        notice._cssk_workflow_write({"xml_attachment_id": foreign.id})
        with self.assertRaisesRegex(UserError, "exported attachment"):
            notice.action_submit()

    def test_manual_channel_attests_retained_export_after_master_data_drift(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        content = notice.xml_attachment_id.raw
        submission = notice.action_create_submission(channel="pfs_manual")
        # Native action returns its form action, not the submission record.
        submission = self.env["cssk.submission"].browse(submission["res_id"])
        self.company.phone = "+421000000000"
        submission.action_attest_manual()
        self.assertEqual(submission.state, "delivered")
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(
            submission.payload_attachment_id, notice.submitted_attachment_id
        )
        self.assertEqual(len(notice.source_history), 1)

    def test_reversed_adjustment_and_own_provision_are_not_tax_credits(self):
        notice = self.notice()
        paid = self.entry(10, debit=self.expense)
        adjustment = self.env["l10n.sk.transaction.tax.adjustment"].create(
            {
                "notice_id": notice.id,
                "move_line_id": paid.line_ids.filtered(
                    lambda line: line.account_id == self.expense
                ).id,
                "source_reference": "Actual external tax",
                "reviewed": True,
                "amount": -10,
            }
        )
        notice.action_compute_lines()
        notice.action_reset_to_draft()
        paid._reverse_moves(cancel=True)
        with self.assertRaisesRegex(UserError, "unreversed"):
            notice.action_compute_lines()
        adjustment.unlink()
        notice.action_compute_lines()
        notice.action_post_provision()
        other = self.notice()
        self.env["l10n.sk.transaction.tax.adjustment"].create(
            {
                "notice_id": other.id,
                "move_line_id": notice.provision_move_id.line_ids.filtered(
                    lambda line: line.account_id == self.expense
                ).id,
                "amount": -40,
                "source_reference": "Not an external tax payment",
                "reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "own provision"):
            other.action_compute_lines()

    def test_external_provision_reverse_is_not_repeated_by_notice(self):
        notice = self.notice()
        notice.action_compute_lines()
        notice.action_post_provision()
        original = notice.provision_move_id
        reversal = original._reverse_moves(cancel=True)
        notice.action_reverse_provision()
        self.assertFalse(notice.provision_move_id)
        self.assertEqual(original.reversal_move_ids, reversal)
        notice.action_post_provision()
        self.assertEqual(len(notice.provision_history_ids), 3)
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.expense
            ).balance,
            40,
        )

    def test_cash_journal_credit_is_not_a_payment_account_transfer(self):
        notice = self.notice(1000)
        cash_journal = self.env["account.journal"].create(
            {
                "name": "Synthetic petty cash",
                "code": "DFTC",
                "type": "cash",
                "company_id": self.company.id,
                "default_account_id": self.cash.id,
            }
        )
        move = self.entry(1000, credit=self.cash, journal=cash_journal)
        notice.source_ids.move_line_id = move.line_ids.filtered(
            lambda line: line.account_id == self.cash
        )
        with self.assertRaisesRegex(UserError, "payment account"):
            notice.action_compute_lines()

    def test_ordinary_accountant_full_flow_post_then_export_without_duplicate_tax(self):
        notice = self.notice().with_user(self.operator)
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 40)
        notice.action_post_provision()
        move = notice.provision_move_id
        self.assertEqual(move.state, "posted")
        self.assertEqual(
            move.line_ids.filtered(
                lambda line: line.account_id == self.expense
            ).balance,
            40,
        )
        self.assertEqual(
            move.line_ids.filtered(lambda line: line.account_id == self.tax).balance,
            -40,
        )
        notice.action_post_provision()
        self.assertEqual(notice.provision_move_id, move)
        notice.action_export_xml()
        self.assertEqual(
            etree.fromstring(notice.xml_attachment_id.raw).findtext("telo/r7"), "40.00"
        )
        notice.action_submit()
        self.assertEqual(notice.submitted_attachment_id, notice.xml_attachment_id)
        self.assertTrue(notice.submission_ids)
        self.assertEqual(len(notice.source_history), 1)
        self.assertFalse(self.operator.has_group("base.group_system"))
        self.assertFalse(self.operator.has_group("account.group_account_manager"))

    def test_cash_and_unreviewed_bank_sources(self):
        notice = self.notice(50000, "cash")
        notice.source_ids.reviewed = False
        with self.assertRaises(UserError):
            notice.action_compute_lines()
        notice.source_ids.reviewed = True
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 400)

    def _negative_recharge_notice(self):
        # FS12/DZPaU/2025/I domestic example: three identified 100000 transactions,
        # their tax 120 plus the repayment's bank tax 40 =>120-120-40=-40.
        notice = self.notice(300000, "recharge_known")
        notice.source_ids.source_amount = "100000"
        notice.source_ids.reviewed = True
        notice.source_ids.copy({"transaction_reference": "Synthetic-original-T2"})
        notice.source_ids[:1].copy({"transaction_reference": "Synthetic-original-T3"})
        already_paid = self.entry(40, debit=self.expense)
        third_party_tax = self.entry(120, debit=self.expense, credit=self.payable)
        notice.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": already_paid.line_ids.filtered(
                                lambda line: line.account_id == self.expense
                            ).id,
                            "amount": -40,
                            "source_reference": "Synthetic actual tax deduction and legal allocation",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        notice.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": third_party_tax.line_ids.filtered(
                                lambda line: line.account_id == self.expense
                            ).id,
                            "amount": -120,
                            "source_reference": "Synthetic original third-party tax-paid receipt and recharge allocation",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        return notice

    def test_negative_tax_is_booked_as_receivable_not_clamped_to_zero(self):
        notice = self._negative_recharge_notice()
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, -40)
        notice.action_post_provision()
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.tax
            ).balance,
            40,
        )
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.expense
            ).balance,
            -40,
        )
        notice.action_export_xml()
        self.assertEqual(
            etree.fromstring(notice.xml_attachment_id.raw).findtext("telo/r7"), "-40.00"
        )

    def test_partial_month_native_export_and_correction_preserve_old_dates(self):
        notice = self.notice(period_from="2026-05-10", period_to="2026-05-25")
        self.file(notice)
        original = notice.xml_attachment_id.raw
        root = etree.fromstring(original)
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/od"), "10.05.2026")
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/do"), "25.05.2026")
        notice.action_reset_to_draft()
        with self.assertRaises(UserError):
            notice.write({"period_from": "2026-05-11"})
        action = notice.action_create_amendment()
        correction = self.env[MODEL].browse(action["res_id"])
        self.assertEqual(correction.period_from, notice.period_from)
        self.assertEqual(correction.period_to, notice.period_to)
        correction.write({"period_from": "2026-05-11"})
        correction.action_compute_lines()
        correction.action_export_xml()
        self.assertEqual(notice.filed_history_ids.raw, original)
        self.assertEqual(
            etree.fromstring(correction.xml_attachment_id.raw).findtext(
                "hlavicka/zdanovacieObdobie/od"
            ),
            "11.05.2026",
        )

    def test_partial_month_checks_native_sources_and_requires_both_dates(self):
        with self.assertRaises(UserError), self.env.cr.savepoint():
            self.notice(period_from="2026-05-10")
        notice = self.notice(period_from="2026-05-21", period_to="2026-05-25")
        with self.assertRaisesRegex(UserError, "exact reported period"):
            notice.action_compute_lines()

    def test_bank_source_cannot_be_reused_in_another_filed_month(self):
        original = self.notice(1000)
        self.file(original)
        later = self.notice(
            1000,
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        later.source_ids.write(
            {
                "move_line_id": original.source_ids.move_line_id.id,
                "source_reference": "Synthetic reused actual bank row",
                "reviewed": True,
            }
        )
        with self.assertRaisesRegex(UserError, "another filed DFT month"):
            later.action_compute_lines()

    def test_effective_correction_releases_a_source_for_its_corrected_month(self):
        original = self.notice(1000)
        self.file(original)
        line = original.source_ids.move_line_id
        archived = original.xml_attachment_id.raw
        action = original.action_create_amendment()
        correction = self.env[MODEL].browse(action["res_id"])
        correction.source_ids.unlink()
        self.file(correction)
        later = self.notice(
            1000,
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        later.source_ids.write(
            {
                "move_line_id": line.id,
                "source_reference": "Synthetic actual transaction corrected to June",
                "reviewed": True,
            }
        )
        later.action_compute_lines()
        self.assertEqual(later.tax_total, 4)
        self.assertEqual(original.filed_history_ids.raw, archived)

    def test_card_usage_and_excluded_payment_are_distinct_facts(self):
        notice = self.notice(
            1000,
            kind="card",
            period="2026-12-01",
            signed_on="2027-01-31",
            filing_on="2027-01-31",
            deadline="2027-02-01",
        )
        notice.source_ids.write(
            {"card_reference": "Synthetic card A", "reviewed": True}
        )
        notice.source_ids.copy(
            {
                "kind": "excluded",
                "card_reference": False,
                "classification_reference": "Synthetic reviewed card payment excluded under section 4(2)",
            }
        )
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 2)

    def test_split_recharge_rows_share_one_cap_and_the_actual_native_payment(self):
        notice = self.notice(30000, "recharge_known")
        notice.source_ids.write({"source_amount": "15000", "reviewed": True})
        notice.source_ids.copy()
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 40)
        self.assertEqual(
            [row["tax"] for row in notice.payload["computed_recharges"]],
            ["40.00", "0.00"],
        )

    def test_partial_recharge_across_months_and_amendments_preserves_tax_and_archives(
        self,
    ):
        def post_file(notice):
            notice.action_compute_lines()
            notice.action_post_provision()
            notice.action_export_xml()
            notice.action_submit()

        first = self.notice(5000, "recharge_known")
        post_file(first)
        second = self.notice(
            20000,
            "recharge_known",
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        post_file(second)
        self.assertEqual(first.tax_total, 20)
        self.assertEqual(second.tax_total, 20)
        archives = first.filed_history_ids.raw, second.filed_history_ids.raw
        self.assertTrue(second.action_check_recharge_dependencies())
        correction = self.env[MODEL].browse(first.action_create_amendment()["res_id"])
        correction.source_ids.write({"source_amount": "2500", "reviewed": True})
        post_file(correction)
        self.assertEqual(correction.tax_total, 10)
        with self.assertRaisesRegex(UserError, "earlier identified recharge"):
            second.action_check_recharge_dependencies()
        later = self.env[MODEL].browse(second.action_create_amendment()["res_id"])
        post_file(later)
        self.assertEqual(later.tax_total, 30)
        self.assertTrue(later.action_check_recharge_dependencies())
        self.assertEqual(
            (first.filed_history_ids.raw, second.filed_history_ids.raw), archives
        )
        booked = (first | second | correction | later).provision_history_ids
        self.assertEqual(
            -sum(
                booked.line_ids.filtered(lambda row: row.account_id == self.tax).mapped(
                    "balance"
                )
            ),
            40,
        )

    def test_excluded_recharge_uses_actual_settlement_and_retains_legal_evidence(self):
        notice = self.notice(30000, "recharge_excluded")
        notice.source_ids.write(
            {
                "classification_reference": "Synthetic original transfer excluded by law",
                "reviewed": True,
            }
        )
        notice.action_compute_lines()
        notice.action_export_xml()
        self.assertEqual(notice.tax_total, 0)
        self.assertEqual(notice.payload["computed_recharges"][0]["tax"], "0.00")
        self.assertEqual(
            float(notice.payload["source_facts"][0]["allocated_source_amount"]), 30000
        )

    def _foreign_refund_notice(self):
        bank = self.env["res.bank"].create(
            {
                "name": "Synthetic foreign bank",
                "bic": "BOFAUS3N",
                "city": "New York",
                "country": self.env.ref("base.us").id,
            }
        )
        account = self.env["res.partner.bank"].create(
            {
                "partner_id": self.company.partner_id.id,
                "company_id": self.company.id,
                "acc_number": "123456789012",
                "bank_id": bank.id,
            }
        )
        notice = self._negative_recharge_notice()
        notice.write(
            {
                "refund_requested": True,
                "refund_bank_id": account.id,
                "refund_date": "2026-06-30",
            }
        )
        return notice, account, bank

    def test_foreign_non_iban_refund_uses_all_native_bank_details_and_valid_xml(self):
        notice, account, bank = self._foreign_refund_notice()
        notice = notice.with_user(self.operator)
        notice.action_compute_lines()
        notice.action_export_xml()
        root = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(root.findtext("telo/vratenieDane/iban"), "")
        details = root.findtext("telo/vratenieDane/ucetVedenyVZahranici")
        for value in (
            account.sanitized_acc_number,
            bank.bic,
            bank.name,
            bank.city,
            "United States",
        ):
            self.assertIn(value, details)
        self.assertEqual(root.findtext("telo/vratenieDane/ziadamVratenie"), "1")

    def test_non_iban_refund_requires_foreign_country_and_complete_bank_master(self):
        notice, account, bank = self._foreign_refund_notice()
        for values in (
            {"country": self.env.ref("base.sk").id},
            {"city": False},
            {"bic": False},
            {"bic": "bad"},
        ):
            old = {
                name: bank[name].id if name == "country" else bank[name]
                for name in values
            }
            bank.write(values)
            with self.assertRaisesRegex(UserError, "non-IBAN refund"):
                notice.action_compute_lines()
            bank.write(old)
        notice.refund_bank_id = account.copy({"partner_id": self.representative.id})
        with self.assertRaisesRegex(UserError, "company's actual refund"):
            notice.action_compute_lines()

    def test_refund_branch_location_is_not_inferred_from_the_bic_country(self):
        notice, account, bank = self._foreign_refund_notice()
        bank.write({"city": "Toronto", "country": self.env.ref("base.ca").id})
        notice.action_compute_lines()
        notice.action_export_xml()
        details = etree.fromstring(notice.xml_attachment_id.raw).findtext(
            "telo/vratenieDane/ucetVedenyVZahranici"
        )
        self.assertIn("Toronto", details)
        self.assertIn("Canada", details)
        self.assertIn("BOFAUS3N", details)

    def test_refund_bank_edit_after_preview_requires_a_new_calculation(self):
        notice, account, bank = self._foreign_refund_notice()
        notice.action_compute_lines()
        bank.city = "Boston"
        with self.assertRaises(UserError):
            notice.action_export_xml()

    def test_correction_posts_only_unbooked_difference_and_retains_original(self):
        original = self.notice(1000)
        original.action_compute_lines()
        original.action_post_provision()
        original.action_export_xml()
        original.action_submit()
        original_bytes, history = (
            original.submitted_attachment_id.raw,
            deepcopy(original.source_history),
        )
        correction = self.env[MODEL].browse(
            original.action_create_amendment()["res_id"]
        )
        correction.write(
            {
                "signed_on": "2026-07-10",
                "filing_on": "2026-07-10",
                "filing_type": "additional",
                "discovery_date": "2026-07-10",
            }
        )
        move = self.entry(2000)
        correction.source_ids.write(
            {
                "move_line_id": move.line_ids.filtered(
                    lambda line: line.account_id == self.bank
                ).id,
                "reviewed": True,
            }
        )
        correction.action_compute_lines()
        self.assertEqual(correction.tax_total, 8)
        correction.action_post_provision()
        self.assertEqual(
            correction.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.tax
            ).balance,
            -4,
        )
        correction.action_export_xml()
        root = etree.fromstring(correction.xml_attachment_id.raw)
        self.assertEqual(
            (
                root.findtext("telo/r7"),
                root.findtext("telo/r8"),
                root.findtext("telo/r9"),
            ),
            ("8.00", "4.00", "4.00"),
        )
        correction.action_submit()
        self.assertEqual(original.submitted_attachment_id.raw, original_bytes)
        self.assertEqual(original.source_history, history)

    def test_unfiled_reverse_recompute_and_repost_uses_native_reversal(self):
        notice = self.notice(1000)
        notice.action_compute_lines()
        notice.action_post_provision()
        original = notice.provision_move_id
        notice.action_reset_to_draft()
        replacement = self.entry(500)
        notice.source_ids.write(
            {
                "move_line_id": replacement.line_ids.filtered(
                    lambda line: line.account_id == self.bank
                ).id,
                "reviewed": True,
            }
        )
        notice.action_compute_lines()
        with self.assertRaisesRegex(UserError, "Reverse"):
            notice.action_post_provision()
        notice.action_reverse_provision()
        self.assertTrue(original.reversal_move_ids)
        notice.action_post_provision()
        moves = notice.provision_history_ids.filtered(
            lambda move: move.state == "posted"
        )
        self.assertEqual(
            sum(
                moves.line_ids.filtered(
                    lambda line: line.account_id == self.tax
                ).mapped("balance")
            ),
            -2,
        )

    def test_workflow_api_defaults_archive_and_current_source_changes(self):
        notice = self.notice()
        with self.assertRaises(UserError):
            notice.write({"payload": {}})
        with self.assertRaises(UserError):
            self.env[MODEL].with_context(default_state="submitted").create({})
        notice.action_compute_lines()
        notice.action_export_xml()
        content = notice.xml_attachment_id.raw
        notice.xml_attachment_id.write({"raw": content})
        notice.xml_attachment_id._migrate()
        with self.assertRaises(UserError):
            notice.xml_attachment_id.write({"raw": b"tampered"})
        with self.assertRaises(UserError):
            notice.source_ids.reviewed = False
        self.company.city = "Changed source city"
        notice.action_submit()
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertTrue(notice.submission_ids)
        self.company.email = "changed@example.invalid"
        notice.action_post_provision()
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.expense
            ).balance,
            40,
        )

    def test_computed_deadline_needs_no_manual_attestation(self):
        notice = self.notice(deadline_reference=False)
        self.file(notice)
        correction = self.env[MODEL].browse(notice.action_create_amendment()["res_id"])
        correction.write(
            {
                "signed_on": "2026-07-01",
                "filing_on": "2026-07-01",
                "filing_type": "corrective",
                "discovery_date": False,
            }
        )
        with self.assertRaisesRegex(UserError, "deadline"):
            correction.action_compute_lines()

    def test_late_recording_of_on_time_regular_filing_warns_and_preserves_xml(self):
        notice = self.notice()
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 6, 30)):
            notice.action_compute_lines()
            notice.action_export_xml()
        original = notice.xml_attachment_id.raw
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 11, 11)):
            notice.action_submit()
        self.assertEqual(notice.state, "submitted")
        self.assertEqual(notice.submitted_attachment_id.raw, original)
        self.assertTrue(
            any(
                "Verify the declared actual filing date" in str(row.body)
                for row in notice.message_ids
            )
        )

    def test_correction_prepared_on_time_but_recorded_later_warns(self):
        notice = self.notice()
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 6, 30)):
            self.file(notice)
            correction = self.env[MODEL].browse(
                notice.action_create_amendment()["res_id"]
            )
            self.assertEqual(correction.filing_type, "corrective")
            correction.action_compute_lines()
            correction.action_export_xml()
        original = correction.xml_attachment_id.raw
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 11, 11)):
            correction.action_submit()
        self.assertEqual(correction.state, "submitted")
        self.assertEqual(correction.submitted_attachment_id.raw, original)
        self.assertTrue(
            any(
                "use an additional notice instead" in str(row.body)
                for row in correction.message_ids
            )
        )

    def test_on_time_recording_does_not_warn_about_backdating(self):
        notice = self.notice()
        with patch("odoo.fields.Date.context_today", return_value=date(2026, 6, 30)):
            self.file(notice)
        self.assertFalse(
            any(
                "Verify the declared actual filing date" in str(row.body)
                for row in notice.message_ids
            )
        )

    def test_domestic_bank_warns_for_foreign_provider_but_allows_special_account(self):
        # Synthetic checksum-valid IBAN, never an instruction to pay it.
        bban = "11000000001234567890"
        number = f"SK{98 - int(bban + '282000') % 97:02d}{bban}"
        bank = self.env["res.partner.bank"].create(
            {
                "partner_id": self.company.partner_id.id,
                "acc_number": number,
            }
        )
        self.company_data["default_journal_bank"].bank_account_id = bank
        for special in (False, True):
            with self.subTest(special_account=special):
                notice = self.notice(grounds_e=special)
                notice.action_compute_lines()
                self.assertEqual(notice.tax_total, 40)
                warning = any(
                    "only foreign-provider payer grounds" in str(row.body)
                    for row in notice.message_ids
                )
                self.assertEqual(warning, not special)

    def test_actual_currency_base_is_independent_of_the_ledger_exchange_rate(self):
        notice = self.notice(4)
        notice.source_ids.unlink()
        usd = self.env.ref("base.USD")
        usd.active = True
        move = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": self.company_data["default_journal_bank"].id,
                "date": "2026-05-20",
                "ref": "SYNTHETIC DFT FX source",
                "line_ids": [
                    Command.create(
                        {
                            "name": "Foreign liability",
                            "account_id": self.payable.id,
                            "debit": 4,
                            "currency_id": usd.id,
                            "amount_currency": 37.49,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Foreign bank disbursement",
                            "account_id": self.bank.id,
                            "credit": 4,
                            "currency_id": usd.id,
                            "amount_currency": -37.49,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        notice.write(
            {
                "source_ids": [
                    Command.create(
                        {
                            "move_line_id": move.line_ids.filtered(
                                lambda line: line.account_id == self.bank
                            ).id,
                            "kind": "transfer",
                            "actual_on": "2026-05-20",
                            "source_reference": "Synthetic reviewed actual foreign bank payment",
                            "euro_quote": "10",
                            "exchange_reference": "Synthetic official dated quote 10 units/EUR",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, 0.01)
        self.assertEqual(notice.payload["rows"][0]["base_eur"], "3.749")
        self.assertEqual(notice.payload["source_facts"][0]["balance"], -4)
        notice.action_export_xml()
        root = etree.fromstring(notice.xml_attachment_id.raw)
        self.assertEqual(
            (root.findtext("telo/r1s1"), root.findtext("telo/r1s2")), ("3.75", "0.01")
        )

    def test_duplicate_tax_credits_cannot_exceed_the_actual_source(self):
        notice = self.notice(1000)
        tax = self.entry(10, debit=self.expense)
        line = tax.line_ids.filtered(lambda row: row.account_id == self.expense)
        notice.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": line.id,
                            "amount": -6,
                            "source_reference": "Synthetic proportional deduction "
                            + str(number),
                            "reviewed": True,
                        }
                    )
                    for number in (1, 2)
                ]
            }
        )
        with self.assertRaisesRegex(UserError, "adjustments exceed"):
            notice.action_compute_lines()

    def test_proportional_third_party_tax_uses_only_the_reviewed_owned_share(self):
        notice = self.notice(30000, "recharge_known")
        # The original payer's receipt is120, of which this company bears2/3.
        # Its ledger records only its80 share; neither the full120 nor a guessed
        # bank-rate calculation is a source for this company's reduction.
        shared_tax = self.entry(80, debit=self.expense, credit=self.payable)
        tax_source = shared_tax.line_ids.filtered(
            lambda line: line.account_id == self.expense
        )
        allocation = "Reviewed paid original tax 120; company share2/3=80; receipt T1"
        notice.adjustment_ids = [
            Command.create(
                {
                    "move_line_id": tax_source.id,
                    "amount": -80,
                    "source_reference": allocation,
                    "reviewed": True,
                }
            )
        ]
        notice.action_compute_lines()
        self.assertEqual(notice.tax_total, -40)
        self.assertEqual(
            notice.payload["adjustments"][0]["source_reference"], allocation
        )
        notice.action_post_provision()
        self.assertEqual(
            notice.provision_move_id.line_ids.filtered(
                lambda line: line.account_id == self.tax
            ).balance,
            40,
        )
        notice.action_reset_to_draft()
        notice.adjustment_ids.write({"amount": -120, "reviewed": True})
        with self.assertRaisesRegex(UserError, "cannot exceed"):
            notice.action_compute_lines()

    def test_future_tax_credit_is_not_a_completed_payment_at_filing(self):
        notice = self.notice(1000)
        tax = self.entry(10, debit=self.expense, date="2026-07-01")
        notice.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": tax.line_ids.filtered(
                                lambda row: row.account_id == self.expense
                            ).id,
                            "amount": -10,
                            "source_reference": "Synthetic future tax debit",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        with self.assertRaisesRegex(UserError, "actual posted tax source"):
            notice.action_compute_lines()

    def test_filed_identity_and_source_archive_survive_reset_and_clear(self):
        notice = self.notice()
        self.file(notice)
        content, history = (
            notice.submitted_attachment_id.raw,
            deepcopy(notice.source_history),
        )
        notice.action_reset_to_draft()
        for values in (
            {"period": "2026-06-01"},
            {"filing_type": "additional"},
            {"original_return_id": notice.id},
        ):
            with self.subTest(values=values), self.assertRaises(UserError):
                notice.write(dict(values, source_ids=[Command.clear()]))
        self.assertEqual(len(notice.source_ids), 1)
        self.assertEqual(notice.submitted_attachment_id.raw, content)
        self.assertEqual(notice.source_history, history)

    def test_recomputed_booked_amount_cannot_be_silently_left_unposted(self):
        notice = self.notice(1000)
        notice.action_compute_lines()
        notice.action_post_provision()
        notice.action_reset_to_draft()
        replacement = self.entry(500)
        notice.source_ids.write(
            {
                "move_line_id": replacement.line_ids.filtered(
                    lambda line: line.account_id == self.bank
                ).id,
                "reviewed": True,
            }
        )
        notice.action_compute_lines()
        with self.assertRaisesRegex(UserError, "Reverse"):
            notice.action_post_provision()

    def test_second_original_is_not_filed_again_for_the_same_month(self):
        first = self.notice()
        self.file(first)
        duplicate = self.notice()
        with self.assertRaisesRegex(UserError, "immediately previous"):
            duplicate.action_compute_lines()

    def test_resident_bank_payment_is_not_reduced_by_an_expense_allocation(self):
        notice = self.notice(1000)
        notice.source_ids.write({"source_amount": "800", "reviewed": True})
        with self.assertRaisesRegex(UserError, "whole actual debit"):
            notice.action_compute_lines()

    def test_invalid_exchange_input_is_a_named_user_error(self):
        notice = self.notice()
        notice.source_ids.write({"euro_quote": "NaN", "reviewed": True})
        with self.assertRaisesRegex(UserError, "Review DFT source inputs"):
            notice.action_compute_lines()

    def test_actual_tax_credit_cannot_be_overallocated_across_filed_months(self):
        paid = self.entry(10, debit=self.expense)
        source = paid.line_ids.filtered(lambda row: row.account_id == self.expense)
        first = self.notice(1000)
        first.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": source.id,
                            "amount": -6,
                            "source_reference": "Synthetic first reviewed allocation from actual tax 10",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        self.file(first)
        second = self.notice(
            1000,
            period="2026-06-01",
            signed_on="2026-07-31",
            filing_on="2026-07-31",
            deadline="2026-07-31",
        )
        second.write(
            {
                "adjustment_ids": [
                    Command.create(
                        {
                            "move_line_id": source.id,
                            "amount": -6,
                            "source_reference": "Synthetic second allocation would exceed actual tax 10",
                            "reviewed": True,
                        }
                    )
                ]
            }
        )
        with self.assertRaisesRegex(UserError, "already allocated"):
            second.action_compute_lines()
        second.adjustment_ids.write({"amount": -4, "reviewed": True})
        second.action_compute_lines()
        self.assertEqual(second.tax_total, 0)
