# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestVatClosing(AccountTestInvoicingCommon):
    """The VAT closing clears the period's tax lines into the settlement
    account, agrees with the return, and closes every line exactly once."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.settlement = cls.env["account.account"].search([
            *cls.env["account.account"]._check_company_domain(cls.company),
            ("code", "=", "343000")], limit=1)
        cls.sale = cls.init_invoice(
            "out_invoice", partner=cls.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=cls.tax_sale_a, post=True)
        cls.bill = cls.init_invoice(
            "in_invoice", partner=cls.partner_a, invoice_date="2026-06-12",
            amounts=[500.0], taxes=cls.tax_purchase_a, post=True)
        out_tag = cls.sale.line_ids.filtered("tax_line_id").tax_tag_ids[:1]
        in_tag = cls.bill.line_ids.filtered("tax_line_id").tax_tag_ids[:1]
        template = cls.env["ir.ui.view"].create({
            "name": "cssk vat closing test", "type": "qweb",
            "arch": "<t t-name='cssk_vat_closing_test'><DPH/></t>"})
        cls.version = cls.env["cssk.vat.return.version"].create({
            "name": "CLOSE", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id, "xml_root_element": "DPH",
            "own_tax_line_code": "rown", "excess_line_code": "rexc",
            "line_def_ids": [
                (0, 0, {"code": "rout", "name": "Output", "kind": "tags",
                        "tag_formula": "-" + out_tag.name, "sequence": 10}),
                (0, 0, {"code": "rin", "name": "Input", "kind": "tags",
                        "tag_formula": in_tag.name, "sequence": 20}),
                (0, 0, {"code": "rown", "name": "Own tax", "kind": "aggregate",
                        "aggregate_formula": "rout - rin", "sequence": 30}),
                (0, 0, {"code": "rexc", "name": "Excess", "kind": "manual",
                        "sequence": 40}),
            ],
            "statement_type_ids": [(0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"})],
        })

    def _return(self, **vals):
        ret = self.env["cssk.vat.return"].create(dict({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30", "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        }, **vals))
        ret.action_compute_lines()
        ret.state = "exported"
        return ret

    def _own(self, ret):
        return ret.line_ids.filtered(lambda l: l.code == "rown")

    def _bal(self, move, account):
        return sum(move.line_ids.filtered(lambda l: l.account_id == account).mapped("balance"))

    def test_closing_clears_tax_accounts_into_settlement(self):
        ret = self._return()
        self.assertAlmostEqual(self._own(ret).value, 115.0)
        ret.action_cssk_vat_closing()
        move = ret.l10n_cssk_closing_move_ids
        self.assertEqual(move.state, "draft")
        self.assertEqual(str(move.date), "2026-06-30")
        out_acc = self.sale.line_ids.filtered("tax_line_id").account_id
        in_acc = self.bill.line_ids.filtered("tax_line_id").account_id
        self.assertAlmostEqual(self._bal(move, out_acc), 230.0)    # output debited away
        self.assertAlmostEqual(self._bal(move, in_acc), -115.0)    # input credited away
        self.assertAlmostEqual(self._bal(move, self.settlement), -115.0)   # liability
        tax_lines = (self.sale | self.bill).line_ids.filtered("tax_line_id")
        self.assertEqual(tax_lines.l10n_cssk_vat_closing_move_id, move)

    def test_a_line_is_closed_once(self):
        ret = self._return()
        ret.action_cssk_vat_closing()
        with self.assertRaisesRegex(UserError, "already closed"):
            ret.action_cssk_vat_closing()

    def test_rounding_within_tolerance_goes_to_rounding_account(self):
        ret = self._return()
        self._own(ret).value = 116.0          # the return rounds up by 1
        ret.action_cssk_vat_closing()
        move = ret.l10n_cssk_closing_move_ids
        loss = self.company._cssk_vat_closing_account(
            "l10n_cssk_vat_rounding_loss_account_id", "548000")
        self.assertAlmostEqual(self._bal(move, loss), 1.0)
        self.assertAlmostEqual(self._bal(move, self.settlement), -116.0)
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0.0)

    def test_disagreement_beyond_tolerance_stops_the_closing(self):
        ret = self._return()
        self._own(ret).value = 200.0
        with self.assertRaisesRegex(UserError, "disagree"):
            ret.action_cssk_vat_closing()
        self.assertFalse(ret.l10n_cssk_closing_move_ids)

    def test_amendment_closes_only_what_is_left(self):
        ret = self._return()
        ret.action_cssk_vat_closing()
        ret.l10n_cssk_closing_move_ids.action_post()
        ret.state = "submitted"
        late = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
            amounts=[100.0], taxes=self.tax_sale_a, post=True)
        amendment = self._return(original_return_id=ret.id)
        self.assertAlmostEqual(self._own(amendment).value, 138.0)
        amendment.action_cssk_vat_closing()
        move = amendment.l10n_cssk_closing_move_ids
        self.assertAlmostEqual(self._bal(move, self.settlement), -23.0)
        self.assertEqual(move.line_ids.filtered(lambda l: l.account_id != self.settlement)
                         .mapped("balance"), [23.0])
        self.assertEqual(late.line_ids.filtered("tax_line_id").l10n_cssk_vat_closing_move_id, move)

    def test_amendment_survives_a_changed_settlement_account(self):
        """The amount an earlier closing moved is frozen on it: switching the
        settlement account before the amendment must not make the amendment
        re-close the original's 115."""
        ret = self._return()
        ret.action_cssk_vat_closing()
        ret.state = "submitted"
        new_settlement = self.env["account.account"].create({
            "name": "VAT settlement 2", "code": "343900", "account_type": "liability_current",
            "company_ids": [(6, 0, self.company.ids)]})
        self.company.l10n_cssk_vat_settlement_account_id = new_settlement
        self.init_invoice("out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
                          amounts=[100.0], taxes=self.tax_sale_a, post=True)
        amendment = self._return(original_return_id=ret.id)
        amendment.action_cssk_vat_closing()
        self.assertAlmostEqual(
            self._bal(amendment.l10n_cssk_closing_move_ids, new_settlement), -23.0)

    def test_deleting_a_closing_frees_its_lines(self):
        ret = self._return()
        ret.action_cssk_vat_closing()
        ret.l10n_cssk_closing_move_ids.unlink()
        ret.action_cssk_vat_closing()
        self.assertEqual(len(ret.l10n_cssk_closing_move_ids), 1)

    def test_draft_return_cannot_be_closed(self):
        ret = self._return()
        ret.state = "draft"
        with self.assertRaises(UserError):
            ret.action_cssk_vat_closing()
