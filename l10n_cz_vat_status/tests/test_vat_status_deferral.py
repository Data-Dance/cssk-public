# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A declared later VAT period does not apply to a non-payer's documents.

``cssk_vat_deduction_date`` (l10n_cssk_core) moves a document onto a later
return and, with a deferral account, its VAT off 343 until then. That is the
§ 73 deferral of a DEDUCTION. An identifikovaná osoba has no deduction
(§ 72 odst. 1); what it has on 343 is the self-assessed liability (§ 108
odst. 2 / odst. 3 písm. a)), declared for the period of its tax point.
"""

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCzVatStatusDeferral(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        ref = cls.env["account.chart.template"].with_company(cls.company).ref
        cls.purch_eu_g = ref("l10n_cz_21_acquisition_goods_eu")
        cls.product = cls.env["product.product"].create({
            "name": "Zboží", "type": "consu", "standard_price": 1000.0})
        cls.partner_de = cls.env["res.partner"].create({
            "name": "Lieferant GmbH", "country_id": cls.env.ref("base.de").id,
            "vat": "DE123456788"})
        cls.deferral = cls.env["account.account"].create({
            "name": "DPH přiznaná později", "code": "343990",
            "account_type": "asset_current",
            "company_ids": [Command.set(cls.company.ids)],
        })
        cls.company.cssk_vat_deferral_account_id = cls.deferral
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_vat_return.dphdp3_type_B")

    # ------------------------------------------------------------------
    def _status(self, date_from, status, **kw):
        return self.env["l10n.cz.vat.status.period"].create(
            dict(company_id=self.company.id, date_from=date_from, status=status, **kw))

    def _taxes_on(self, duzp):
        status = self.company._l10n_cz_vat_status_on(fields.Date.to_date(duzp))
        return self.company._l10n_cz_vat_status_map_taxes(self.purch_eu_g, status)

    def _bill(self, duzp, declared):
        """An intra-Community acquisition of goods, self-assessed."""
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_de.id,
            "invoice_date": duzp, "date": duzp,
            "taxable_supply_date": duzp,
            "cssk_vat_deduction_date": declared,
            "invoice_line_ids": [Command.create({
                "product_id": self.product.id, "price_unit": 1000.0,
                "quantity": 1,
                "tax_ids": [Command.set(self._taxes_on(duzp).ids)]})],
        })
        bill.action_post()
        return bill

    @staticmethod
    def _live(move):
        return move.cssk_vat_deferral_move_ids.filtered(
            lambda m: m.state != "cancel")

    def _return(self, date_from, date_to):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "period_type": "month",
            "date_from": date_from, "date_to": date_to,
        })
        ret.action_compute_lines()
        return ret

    def _output_tax(self, date_from, date_to):
        """DPHDP3 ř. 3 daň: the self-assessed acquisition's liability."""
        ret = self._return(date_from, date_to)
        return ret.line_ids.filtered(lambda l: l.code == "dan_pzb23").value

    def _in_period(self, move, date_from, date_to):
        ret = self.env["cssk.vat.return"].new({"company_id": self.company.id})
        return move.id in ret._cssk_period_move_ids(
            self.company, fields.Date.to_date(date_from),
            fields.Date.to_date(date_to))

    # ------------------------------------------------------------------
    def test_identified_person_liability_is_not_deferred(self):
        """The failing case: § 108 odst. 2 liability, tax point in March, a
        declared date in May. Nothing leaves 343 and March reports it."""
        self._status("2026-01-01", "identified", legal_basis="identified_6g")
        bill = self._bill("2026-03-10", "2026-05-10")
        self.assertEqual(
            bill.invoice_line_ids.tax_ids.l10n_cz_vat_status_kind, "selfassessed")
        self.assertTrue(bill._cssk_vat_deferral_source_lines(),
                        "the liability leg does stand on 343")
        self.assertFalse(bill.cssk_vat_deferral_move_ids)
        self.assertTrue(bill.l10n_cz_vat_status_declared_date_note)
        self.assertTrue(self._in_period(bill, "2026-03-01", "2026-03-31"))
        self.assertFalse(self._in_period(bill, "2026-05-01", "2026-05-31"))
        self.assertAlmostEqual(self._output_tax("2026-03-01", "2026-03-31"), 210.0)
        self.assertAlmostEqual(self._output_tax("2026-05-01", "2026-05-31"), 0.0)

    def test_payer_document_still_defers(self):
        """History exists, but the document falls on a plátce day."""
        self._status("2026-06-01", "identified", legal_basis="identified_6g")
        bill = self._bill("2026-03-10", "2026-05-10")
        self.assertEqual(bill.invoice_line_ids.tax_ids, self.purch_eu_g)
        self.assertEqual(len(self._live(bill)), 2)
        self.assertFalse(bill.l10n_cz_vat_status_declared_date_note)
        self.assertFalse(self._in_period(bill, "2026-03-01", "2026-03-31"))
        self.assertTrue(self._in_period(bill, "2026-05-01", "2026-05-31"))
        self.assertAlmostEqual(self._output_tax("2026-03-01", "2026-03-31"), 0.0)
        self.assertAlmostEqual(self._output_tax("2026-05-01", "2026-05-31"), 210.0)

    def test_no_history_defers_exactly_as_before(self):
        self.assertFalse(self.company.l10n_cz_vat_status_period_ids)
        bill = self._bill("2026-03-10", "2026-05-10")
        self.assertFalse(bill._l10n_cz_vat_status_ignores_declared_date())
        self.assertEqual(len(self._live(bill)), 2)
        self.assertFalse(bill.l10n_cz_vat_status_declared_date_note)
        self.assertFalse(self._in_period(bill, "2026-03-01", "2026-03-31"))
        self.assertTrue(self._in_period(bill, "2026-05-01", "2026-05-31"))

    def test_boundary_day_belongs_to_the_new_status(self):
        """The status row's first day is inclusive on the new status."""
        self._status("2026-04-01", "identified", legal_basis="identified_6g")
        last_payer_day = self._bill("2026-03-31", "2026-05-10")
        first_identified_day = self._bill("2026-04-01", "2026-06-10")
        self.assertEqual(len(self._live(last_payer_day)), 2)
        self.assertFalse(first_identified_day.cssk_vat_deferral_move_ids)
        self.assertTrue(self._in_period(last_payer_day, "2026-05-01", "2026-05-31"))
        self.assertTrue(self._in_period(
            first_identified_day, "2026-04-01", "2026-04-30"))
        self.assertFalse(self._in_period(
            first_identified_day, "2026-06-01", "2026-06-30"))

    def test_history_edit_withdraws_and_rebuilds_the_deferral(self):
        bill = self._bill("2026-03-10", "2026-05-10")
        first = self._live(bill)
        self.assertEqual(len(first), 2)
        period = self._status("2026-03-01", "identified", legal_basis="identified_6g")
        self.assertFalse(self._live(bill))
        self.assertEqual(set(first.mapped("state")), {"cancel"})
        self.assertTrue(self._in_period(bill, "2026-03-01", "2026-03-31"))
        period.unlink()
        self.assertEqual(len(self._live(bill)), 2)
        self.assertTrue(self._in_period(bill, "2026-05-01", "2026-05-31"))

    def test_history_edit_into_a_locked_period_is_recorded_not_refused(self):
        bill = self._bill("2026-03-10", "2026-05-10")
        entries = self._live(bill)
        self.company.fiscalyear_lock_date = "2026-03-31"
        self._status("2026-03-01", "identified", legal_basis="identified_6g")
        # The history is recorded; the entries could not be withdrawn and
        # the document says so.
        self.assertTrue(self.company.l10n_cz_vat_status_period_ids)
        self.assertEqual(self._live(bill), entries)
        self.assertIn("VAT-deferral", bill.message_ids[:1].body)

    def test_history_edit_leaves_documents_whose_status_did_not_change(self):
        """A plátce bill posted before the deferral account was set has no
        entries. A status change that does not reach it must not add them."""
        self.company.cssk_vat_deferral_account_id = False
        bill = self._bill("2026-03-10", "2026-05-10")
        self.company.cssk_vat_deferral_account_id = self.deferral
        self.assertFalse(bill.cssk_vat_deferral_move_ids)
        self._status("2026-08-01", "identified", legal_basis="identified_6g")
        self.assertFalse(bill.cssk_vat_deferral_move_ids)
