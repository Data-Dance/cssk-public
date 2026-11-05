# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSepaSymbols(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("account_payment_order.group_account_payment")
        cls.company = cls.env.company
        cls.company.partner_id.country_id = cls.env.ref("base.sk")
        cls.journal = cls.company_data["default_journal_bank"]
        cls.journal.bank_account_id = cls.env["res.partner.bank"].create({
            "acc_number": "SK8402000000003456789012",
            "partner_id": cls.company.partner_id.id,
        })
        sepa = cls.env["account.payment.method"].search(
            [("code", "=", "sepa_credit_transfer"), ("payment_type", "=", "outbound")]
        )
        if sepa not in cls.journal.outbound_payment_method_line_ids.payment_method_id:
            cls.journal.outbound_payment_method_line_ids = [
                Command.create({"payment_method_id": sepa.id})
            ]
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "SEPA transfer",
            "company_id": cls.company.id,
            "payment_method_id": sepa.id,
            "bank_account_link": "fixed",
            "fixed_journal_id": cls.journal.id,
        })
        cls.partner_a.bank_ids = [
            Command.create({"acc_number": "SK5811000000002629101234"})
        ]

    def _bill(self, ref, amount=100.0, **symbols):
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-11-01",
            "invoice_date_due": "2026-11-15",
            "ref": ref,
            "invoice_line_ids": [
                Command.create({"name": "stuff", "quantity": 1, "price_unit": amount})
            ],
        })
        bill.action_post()
        for field, value in symbols.items():
            bill[f"l10n_cssk_{field}_symbol"] = value
        return bill

    def _export(self, *bills, placement=None):
        if placement:
            self.journal.l10n_cssk_sepa_symbol_placement = placement
        order = self.env["account.payment.order"].create({
            "payment_mode_id": self.mode.id,
            "payment_type": "outbound",
            "journal_id": self.journal.id,
        })
        for bill in bills:
            bill.line_ids.filtered(
                lambda line: line.account_id.account_type == "liability_payable"
            ).create_payment_line_from_move_line(order)
        order.draft2open()
        order.open2generated()
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "account.payment.order"), ("res_id", "=", order.id)],
            limit=1,
        )
        root = etree.fromstring(base64.b64decode(attachment.datas))
        ns = {"p": root.nsmap[None]}
        transfers = root.findall(".//p:CdtTrfTxInf", ns)
        return [
            (
                tx.findtext("p:PmtId/p:EndToEndId", namespaces=ns),
                tx.findtext("p:RmtInf/p:Ustrd", namespaces=ns),
            )
            for tx in transfers
        ]

    def test_a_slovak_bank_journal_defaults_to_the_end_to_end_id(self):
        czech = self.env["account.journal"].new({"company_id": self.company.id})
        self.company.account_fiscal_country_id = self.env.ref("base.cz")
        czech._compute_l10n_cssk_sepa_symbol_placement()
        self.assertEqual(czech.l10n_cssk_sepa_symbol_placement, "ustrd")
        slovak = self.env["account.journal"].new({"company_id": self.company.id})
        self.company.account_fiscal_country_id = self.env.ref("base.sk")
        slovak._compute_l10n_cssk_sepa_symbol_placement()
        self.assertEqual(slovak.l10n_cssk_sepa_symbol_placement, "end_to_end")
        german = self.env["account.journal"].new({"company_id": self.company.id})
        self.company.account_fiscal_country_id = self.env.ref("base.de")
        german._compute_l10n_cssk_sepa_symbol_placement()
        self.assertEqual(german.l10n_cssk_sepa_symbol_placement, "none")

    def test_end_to_end_id_carries_all_three_symbols(self):
        bill = self._bill("2026114455", constant="0308", specific="77")
        [(e2e, _ustrd)] = self._export(bill, placement="end_to_end")
        self.assertEqual(e2e, "/VS2026114455/SS77/KS0308")

    def test_remittance_info_carries_the_symbols(self):
        bill = self._bill("2026114455", constant="0308")
        [(e2e, ustrd)] = self._export(bill, placement="ustrd")
        self.assertTrue(ustrd.endswith("/VS/2026114455/KS/0308"), ustrd)
        self.assertNotIn("/VS", e2e)

    def test_no_symbols_leaves_the_file_as_oca_writes_it(self):
        bill = self._bill("2026114455")
        [(e2e, ustrd)] = self._export(bill, placement="none")
        self.assertNotIn("/VS", e2e)
        self.assertNotIn("/VS", ustrd or "")

    def test_bills_with_different_symbols_are_separate_transfers(self):
        """Merged into one transfer, the supplier could match neither bill."""
        first = self._bill("2026000001")
        second = self._bill("2026000002")
        result = self._export(first, second, placement="end_to_end")
        self.assertEqual(sorted(e2e for e2e, _u in result),
                         ["/VS2026000001", "/VS2026000002"])

    def test_without_symbol_export_bills_group_as_oca_does(self):
        first = self._bill("2026000001")
        second = self._bill("2026000002")
        result = self._export(first, second, placement="none")
        self.assertEqual(len(result), 1)

    def test_a_long_message_keeps_the_symbols_whole(self):
        bill = self._bill("X" * 150 + "2026114455")
        bill.l10n_cssk_variable_symbol = "2026114455"
        [(_e2e, ustrd)] = self._export(bill, placement="ustrd")
        self.assertLessEqual(len(ustrd), 140)
        self.assertTrue(ustrd.endswith("/VS/2026114455"), ustrd)
