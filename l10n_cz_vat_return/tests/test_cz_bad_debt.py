# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Bad-debt corrections land on ř. 33 / ř. 34 and on no ordinary row."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzBadDebt(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        ref = cls.env["account.chart.template"].ref
        cls.sale21 = ref("l10n_cz_21_domestic_supplies")
        cls.purchase21 = ref("l10n_cz_21_receipt_domestic_supplies")
        cls.partner = cls.env["res.partner"].create({
            "name": "Dlužník s.r.o.", "vat": "CZ46342958",
            "country_id": cls.env.ref("base.cz").id})

    def _doc(self, move_type, tax, amount, flag=False, date="2025-06-15"):
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": self.partner.id,
            # l10n_cz defaults the DUZP to TODAY, not the invoice date.
            "invoice_date": date, "date": date, "taxable_supply_date": date,
            "l10n_cz_bad_debt": flag,
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        move.action_post()
        return move

    def _return(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_type_B").id,
            "period_type": "month",
            "date_from": "2025-06-01", "date_to": "2025-06-30",
        })
        ret.action_compute_lines()
        return ret

    def _line(self, ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code)

    def test_a_creditor_correction_goes_to_r33_not_r1(self):
        self._doc("out_invoice", self.sale21, 1000.0)
        self._doc("out_refund", self.sale21, 400.0, flag="P")
        ret = self._return()
        # ř. 1 carries the sale alone; the correction does not reduce it.
        self.assertAlmostEqual(self._line(ret, "obrat23").value, 1000.0)
        self.assertAlmostEqual(self._line(ret, "dan23").value, 210.0)
        opr = self._line(ret, "opr_verit")
        self.assertAlmostEqual(opr.value, 84.0)
        self.assertTrue(opr.source_reconciles)
        self.assertTrue(self._line(ret, "dan23").source_reconciles)

    def test_a_debtor_correction_goes_to_r34(self):
        self._doc("in_invoice", self.purchase21, 1000.0)
        self._doc("in_refund", self.purchase21, 1000.0, flag="P")
        ret = self._return()
        # ř. 40 (odp_tuz23_nar) carries the bill alone, not the correction.
        self.assertAlmostEqual(self._line(ret, "odp_tuz23_nar").value, 210.0)
        self.assertAlmostEqual(self._line(ret, "pln23").value, 1000.0)
        opr = self._line(ret, "opr_dluz")
        self.assertEqual(opr.kind, "tags")
        self.assertAlmostEqual(opr.value, 210.0)
        self.assertTrue(opr.source_reconciles)

    def test_the_old_section_44_is_only_for_supplies_to_march_2019(self):
        origin = self._doc("out_invoice", self.sale21, 1000.0, date="2025-01-10")
        refund = origin._reverse_moves()
        with self.assertRaisesRegex(ValidationError, "31. 3. 2019"):
            refund.l10n_cz_bad_debt = "A"
        refund.l10n_cz_bad_debt = "P"

    def test_the_old_section_44_is_accepted_for_an_old_supply(self):
        origin = self._doc("out_invoice", self.sale21, 1000.0, date="2019-02-10")
        refund = origin._reverse_moves()
        refund.l10n_cz_bad_debt = "A"
        self.assertEqual(refund.l10n_cz_bad_debt, "A")
