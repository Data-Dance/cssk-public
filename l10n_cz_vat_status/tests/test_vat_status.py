# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCzVatStatus(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        ref = cls.env["account.chart.template"].with_company(cls.company).ref
        cls.ref = ref
        cls.sale21 = ref("l10n_cz_21_domestic_supplies")
        cls.sale_eu_s = ref("l10n_cz_supply_service_eu")
        cls.purch21 = ref("l10n_cz_21_receipt_domestic_supplies")
        cls.purch_eu_g = ref("l10n_cz_21_acquisition_goods_eu")
        cls.purch_eu_s = ref("l10n_cz_21_receipt_service_person_eu")
        cls.purch_rc = ref("l10n_cz_21_tax_reverse_charge_scheme")
        cls.purch_import = ref("l10n_cz_21_import_goods")
        cls.product = cls.env["product.product"].create({
            "name": "Zboží", "type": "consu", "lst_price": 1000.0,
            "standard_price": 1000.0,
            "taxes_id": [Command.set(cls.sale21.ids)],
            "supplier_taxes_id": [Command.set(cls.purch21.ids)],
        })
        cls.partner_cz = cls.env["res.partner"].create({
            "name": "Odběratel s.r.o.", "country_id": cls.env.ref("base.cz").id})
        cls.partner_de = cls.env["res.partner"].create({
            "name": "Lieferant GmbH", "country_id": cls.env.ref("base.de").id,
            "vat": "DE123456788"})
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_vat_return.dphdp3_type_B")

    # ------------------------------------------------------------------
    def _status(self, date_from, status, **kw):
        return self.env["l10n.cz.vat.status.period"].create(
            dict(company_id=self.company.id, date_from=date_from, status=status, **kw))

    def _move(self, move_type, duzp, partner=None, taxes=None, price=1000.0,
              post=False):
        line = {"product_id": self.product.id, "price_unit": price, "quantity": 1}
        if taxes is not None:
            line["tax_ids"] = [Command.set(taxes.ids)]
        move = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": (partner or self.partner_cz).id,
            "invoice_date": duzp,
            "taxable_supply_date": duzp,
            "invoice_line_ids": [Command.create(line)],
        })
        if post:
            move.action_post()
        return move

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

    @staticmethod
    def _v(ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    # ------------------------------------------------------------------
    # No history: nothing changes
    # ------------------------------------------------------------------
    def test_no_history_is_exactly_the_old_behaviour(self):
        self.assertFalse(self.company.l10n_cz_vat_status_period_ids)
        self.assertEqual(self.company._l10n_cz_typ_platce(date(2026, 3, 31)), "P")
        self.assertEqual(self.company._l10n_cz_vat_status_on(date(2026, 3, 1)), "payer")
        inv = self._move("out_invoice", "2026-03-10", post=True)
        self.assertEqual(inv.invoice_line_ids.tax_ids, self.sale21)
        self.assertAlmostEqual(inv.amount_tax, 210.0)
        self.assertFalse(inv.l10n_cz_vat_status)
        self.assertTrue(inv.l10n_cz_vat_status_is_tax_document)
        self.assertFalse(inv.l10n_cz_vat_status_print_note)
        # No twin taxes appear in a company that never records a status.
        twins = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", self.company.id),
            ("l10n_cz_vat_status_source_id", "!=", False)])
        self.assertFalse(twins)

    def test_a_payer_only_history_changes_nothing_either(self):
        self._status("2020-01-01", "payer", legal_basis="payer_6_1")
        inv = self._move("out_invoice", "2026-03-10", post=True)
        self.assertEqual(inv.invoice_line_ids.tax_ids, self.sale21)
        self.assertEqual(self.company._l10n_cz_typ_platce(date(2026, 3, 31)), "P")

    # ------------------------------------------------------------------
    # The history itself
    # ------------------------------------------------------------------
    def test_history_is_change_points_with_inclusive_first_day(self):
        self._status("2026-01-01", "non_payer")
        p = self._status("2026-07-01", "payer")
        first = self.company.l10n_cz_vat_status_period_ids.sorted("date_from")[0]
        self.assertEqual(first.date_to, date(2026, 6, 30))
        self.assertFalse(p.date_to)
        on = self.company._l10n_cz_vat_status_on
        self.assertEqual(on(date(2025, 12, 31)), "payer")  # before history
        self.assertEqual(on(date(2026, 1, 1)), "non_payer")
        self.assertEqual(on(date(2026, 6, 30)), "non_payer")
        self.assertEqual(on(date(2026, 7, 1)), "payer")
        segs = self.company._l10n_cz_vat_status_segments(
            date(2026, 6, 1), date(2026, 7, 31))
        self.assertEqual(segs, [
            (date(2026, 6, 1), date(2026, 6, 30), "non_payer"),
            (date(2026, 7, 1), date(2026, 7, 31), "payer")])

    def test_legal_basis_proposes_the_day_the_act_names(self):
        propose = self.env["l10n.cz.vat.status.period"]._propose_date_from
        # § 6 odst. 1: from 1 January of the following year.
        self.assertEqual(propose("payer_6_1", date(2025, 11, 20)), date(2026, 1, 1))
        # § 6 odst. 2: the day after the threshold was exceeded.
        self.assertEqual(propose("payer_6_2", date(2026, 5, 14)), date(2026, 5, 15))
        # § 107b odst. 3: the day after the decision was notified.
        self.assertEqual(propose("non_payer_107b_3", date(2026, 6, 30)), date(2026, 7, 1))
        # § 106 odst. 8 písm. a): the day the decision became final.
        self.assertEqual(propose("non_payer_106_8", date(2026, 6, 30)), date(2026, 6, 30))
        # § 6g: from the day of the first acquisition.
        self.assertEqual(propose("identified_6g", date(2026, 2, 3)), date(2026, 2, 3))

    def test_legal_basis_must_match_status(self):
        with self.assertRaises(ValidationError):
            self._status("2026-01-01", "payer", legal_basis="non_payer_107b_3")

    # ------------------------------------------------------------------
    # typ_platce
    # ------------------------------------------------------------------
    def test_typ_platce_follows_the_status_on_the_date(self):
        self._status("2024-01-01", "non_payer")
        self._status("2025-03-01", "identified", legal_basis="identified_6g")
        self._status("2026-01-01", "payer", legal_basis="payer_6_1")
        typ = self.company._l10n_cz_typ_platce
        self.assertEqual(typ(date(2024, 6, 30)), "N")
        self.assertEqual(typ(date(2025, 3, 31)), "I")
        self.assertEqual(typ(date(2026, 1, 31)), "P")

    def test_dphdp3_export_files_typ_platce_i(self):
        self._status("2025-01-01", "identified", legal_basis="identified_6g")
        ret = self._return("2025-06-01", "2025-06-30")
        ret.action_export_xml()
        import base64

        from lxml import etree
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(root.find(".//VetaD").get("typ_platce"), "I")

    # ------------------------------------------------------------------
    # Neplátce
    # ------------------------------------------------------------------
    def test_non_payer_invoice_carries_no_vat_and_is_no_tax_document(self):
        self._status("2026-01-01", "non_payer", legal_basis="non_payer_initial")
        inv = self._move("out_invoice", "2026-03-10", post=True)
        self.assertFalse(inv.invoice_line_ids.tax_ids)
        self.assertAlmostEqual(inv.amount_tax, 0.0)
        self.assertAlmostEqual(inv.amount_total, 1000.0)
        self.assertEqual(inv.l10n_cz_vat_status, "non_payer")
        self.assertFalse(inv.l10n_cz_vat_status_is_tax_document)
        self.assertEqual(inv.l10n_cz_vat_status_print_note, "Nejsem plátce DPH.")
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", inv.ids)[0].decode()
        self.assertIn("Nejsem plátce DPH.", html)
        self.assertNotIn('name="taxable_supply_date"', html)

    def test_non_payer_input_vat_goes_to_cost_not_343(self):
        self._status("2026-01-01", "non_payer")
        bill = self._move("in_invoice", "2026-03-10", post=True)
        tax = bill.invoice_line_ids.tax_ids
        self.assertEqual(tax.l10n_cz_vat_status_source_id, self.purch21)
        self.assertEqual(tax.l10n_cz_vat_status_kind, "nondeductible")
        self.assertAlmostEqual(bill.amount_total, 1210.0)
        expense = bill.invoice_line_ids.account_id
        on_expense = bill.line_ids.filtered(lambda l: l.account_id == expense)
        self.assertAlmostEqual(sum(on_expense.mapped("balance")), 1210.0)
        self.assertFalse(bill.line_ids.filtered(
            lambda l: l.account_id.code and l.account_id.code.startswith("343")))
        self.assertFalse(bill.line_ids.tax_tag_ids)
        # No KH section: B2 is for a deduction the company does not have.
        self.assertFalse(bill.line_ids.filtered("cssk_control_section_code"))

    def test_non_payer_kh_cannot_be_computed(self):
        self._status("2026-01-01", "non_payer")
        version = self.env["cssk.control.statement.version"].search([
            ("country_id.code", "=", "CZ")], limit=1)
        st_type = self.env["cssk.control.statement.type"].search([
            ("country_id.code", "=", "CZ")], limit=1)
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": version.id,
            "statement_type_id": st_type.id, "period_type": "month",
            "date_from": "2026-03-01", "date_to": "2026-03-31"})
        with self.assertRaisesRegex(UserError, "101c"):
            st.action_compute_lines()

    def test_posting_a_contradicting_tax_is_refused(self):
        self._status("2026-01-01", "non_payer")
        inv = self._move("out_invoice", "2026-03-10", taxes=self.sale21)
        self.assertTrue(inv.l10n_cz_vat_status_warning)
        with self.assertRaises(UserError):
            inv.action_post()
        inv.action_l10n_cz_vat_status_apply_taxes()
        self.assertFalse(inv.invoice_line_ids.tax_ids)
        self.assertFalse(inv.l10n_cz_vat_status_warning)
        inv.action_post()
        self.assertEqual(inv.state, "posted")

    # ------------------------------------------------------------------
    # Identifikovaná osoba
    # ------------------------------------------------------------------
    def test_identified_person_domestic_sale_has_no_vat(self):
        self._status("2026-01-01", "identified", legal_basis="identified_6h")
        inv = self._move("out_invoice", "2026-03-10", post=True)
        self.assertFalse(inv.invoice_line_ids.tax_ids)
        self.assertFalse(inv.l10n_cz_vat_status_is_tax_document)
        self.assertIn("identifikovaná osoba", inv.l10n_cz_vat_status_print_note)

    def test_identified_person_keeps_the_eu_service_for_the_summary(self):
        """§ 102 odst. 3 písm. a): its § 9 odst. 1 services go to the SH."""
        self._status("2026-01-01", "identified", legal_basis="identified_6i")
        mapped = self.company._l10n_cz_vat_status_map_taxes(
            self.sale_eu_s, "identified")
        self.assertEqual(mapped, self.sale_eu_s)
        inv = self._move("out_invoice", "2026-03-10", partner=self.partner_de,
                         taxes=self.sale_eu_s, post=True)
        self.assertEqual(inv.invoice_line_ids.tax_ids, self.sale_eu_s)
        # § 28 odst. 3: this one IS a daňový doklad.
        self.assertTrue(inv.l10n_cz_vat_status_is_tax_document)
        # ...and a neplátce has no such supply to report.
        self.assertFalse(self.company._l10n_cz_vat_status_map_taxes(
            self.sale_eu_s, "non_payer"))

    def test_identified_person_self_assesses_eu_goods_without_deduction(self):
        self._status("2026-01-01", "identified", legal_basis="identified_6g")
        twin = self.company._l10n_cz_vat_status_map_taxes(
            self.purch_eu_g, "identified")
        self.assertEqual(twin.l10n_cz_vat_status_source_id, self.purch_eu_g)
        self.assertEqual(twin.l10n_cz_vat_status_kind, "selfassessed")
        bill = self._move("in_invoice", "2026-03-10", partner=self.partner_de,
                          taxes=twin, post=True)
        # The supplier is paid the net price; the tax is owed, not deducted.
        self.assertAlmostEqual(bill.amount_total, 1000.0)
        expense = bill.invoice_line_ids.account_id
        self.assertAlmostEqual(sum(bill.line_ids.filtered(
            lambda l: l.account_id == expense).mapped("balance")), 1210.0)
        names = set(bill.line_ids.tax_tag_ids.mapped("name"))
        self.assertIn("VAT 3 Tax", names)
        self.assertIn("VAT 3 Base", names)
        self.assertFalse({n for n in names if n.startswith("VAT 4")})
        # KH is for a plátce only.
        self.assertFalse(bill.line_ids.filtered("cssk_control_section_code"))
        ret = self._return("2026-03-01", "2026-03-31")
        self.assertAlmostEqual(self._v(ret, "dan_pzb23"), 210.0)
        self.assertAlmostEqual(self._v(ret, "p_zb23"), 1000.0)
        self.assertAlmostEqual(self._v(ret, "od_zdp23"), 0.0)
        self.assertAlmostEqual(self._v(ret, "nar_zdp23"), 0.0)

    def test_deduction_tagging_pass_leaves_the_twins_alone(self):
        """l10n_cz_vat_return tags ř. 43/44 onto every two-legged purchase
        tax. Run it again after the twins exist: they must stay untagged."""
        self._status("2026-01-01", "identified")
        self.company._cz_tag_selfassessed_deduction()
        twins = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", self.company.id),
            ("l10n_cz_vat_status_kind", "=", "selfassessed")])
        self.assertTrue(twins)
        tags = (twins.invoice_repartition_line_ids
                | twins.refund_repartition_line_ids).tag_ids.mapped("name")
        self.assertFalse([t for t in tags if t.startswith(("VAT 43", "VAT 44"))])
        # ...while the plátce tax keeps its deduction.
        self.assertIn("VAT 43 Total",
                      self.purch_eu_g.invoice_repartition_line_ids.tag_ids.mapped("name"))

    def test_identified_person_services_received_and_what_it_does_not_owe(self):
        self._status("2026-01-01", "identified")
        m = self.company._l10n_cz_vat_status_map_taxes
        # § 108 odst. 3 písm. a) bod 1: services from abroad — owed, no deduction.
        self.assertEqual(m(self.purch_eu_s, "identified").l10n_cz_vat_status_kind,
                         "selfassessed")
        # § 108 odst. 4 písm. a): domestic reverse charge is plátce-only; the
        # supplier charges ordinary VAT, which is not deductible.
        self.assertEqual(m(self.purch_rc, "identified").l10n_cz_vat_status_kind,
                         "nondeductible")
        # § 108 odst. 4 písm. c) / odst. 5 písm. a): import VAT goes to customs.
        self.assertFalse(m(self.purch_import, "identified"))
        # Domestic input VAT: no deduction (§ 72 odst. 1).
        self.assertEqual(m(self.purch21, "identified").l10n_cz_vat_status_kind,
                         "nondeductible")

    # ------------------------------------------------------------------
    # Mid-year change
    # ------------------------------------------------------------------
    def test_mid_year_change_decides_by_duzp_and_remaps_both_ways(self):
        self._status("2026-01-01", "non_payer")
        self._status("2026-07-01", "payer", legal_basis="payer_6_2",
                     event_date=date(2026, 6, 30))
        before = self._move("out_invoice", "2026-06-30", post=True)
        after = self._move("out_invoice", "2026-07-01", post=True)
        self.assertFalse(before.invoice_line_ids.tax_ids)
        self.assertEqual(after.invoice_line_ids.tax_ids, self.sale21)
        # A bill: same rule on the purchase side.
        bill = self._move("in_invoice", "2026-06-15")
        self.assertEqual(bill.invoice_line_ids.tax_ids.l10n_cz_vat_status_source_id,
                         self.purch21)
        bill.taxable_supply_date = "2026-07-02"
        bill._onchange_l10n_cz_vat_status_date()
        self.assertEqual(bill.invoice_line_ids.tax_ids, self.purch21)
        bill.taxable_supply_date = "2026-06-15"
        bill._onchange_l10n_cz_vat_status_date()
        self.assertEqual(bill.invoice_line_ids.tax_ids.l10n_cz_vat_status_kind,
                         "nondeductible")

    def test_duzp_wins_over_invoice_date(self):
        self._status("2026-07-01", "non_payer", legal_basis="non_payer_107b_3")
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner_cz.id,
            "invoice_date": "2026-07-05", "taxable_supply_date": "2026-06-30",
            "invoice_line_ids": [Command.create({
                "product_id": self.product.id, "price_unit": 1000.0})],
        })
        self.assertEqual(inv.l10n_cz_vat_status, "payer")
        self.assertEqual(inv.invoice_line_ids.tax_ids, self.sale21)

    def test_credit_note_follows_the_invoice_it_corrects(self):
        inv = self._move("out_invoice", "2026-05-10", post=True)
        self._status("2026-06-01", "non_payer", legal_basis="non_payer_106_8")
        refund = inv._reverse_moves(default_values_list=[{
            "invoice_date": "2026-06-10", "taxable_supply_date": "2026-06-10"}])
        self.assertEqual(refund._l10n_cz_vat_status_date(), date(2026, 5, 10))
        self.assertEqual(refund.l10n_cz_vat_status, "payer")
        refund.action_post()
        self.assertEqual(refund.invoice_line_ids.tax_ids, self.sale21)

    def test_mixed_period_kh_keeps_only_payer_days(self):
        self._status("2026-03-16", "non_payer", legal_basis="non_payer_107b_3")
        payer_bill = self._move("in_invoice", "2026-03-10", post=True)
        non_payer_bill = self._move("in_invoice", "2026-03-20", post=True)
        self.assertTrue(payer_bill.line_ids.filtered("cssk_control_section_code"))
        self.assertFalse(non_payer_bill.line_ids.filtered("cssk_control_section_code"))
        # The typ_platce is the status on the return's last day.
        self.assertEqual(self.company._l10n_cz_typ_platce(date(2026, 3, 31)), "N")

    def test_history_change_reclassifies_posted_kh_lines(self):
        bill = self._move("in_invoice", "2026-03-10", post=True)
        self.assertTrue(bill.line_ids.filtered("cssk_control_section_code"))
        period = self._status("2026-03-01", "non_payer")
        self.assertFalse(bill.line_ids.filtered("cssk_control_section_code"))
        period.unlink()
        self.assertTrue(bill.line_ids.filtered("cssk_control_section_code"))

    def test_twins_are_not_cloned_into_historical_rates(self):
        self._status("2026-01-01", "identified")
        clones = self.company._cssk_create_historic_vat_taxes()
        self.assertFalse(clones.filtered(
            lambda t: "(no deduction)" in t.name or "(identified person)" in t.name))

    def test_a_tax_that_cannot_be_twinned_blocks_instead_of_slipping_through(self):
        """A self-assessed tax of an unexpected shape gets no identified-person
        twin. Mapping keeps it — and posting must say so rather than let the
        plátce tax, with its deduction, through (GPT-5.3-Codex review)."""
        odd = self.purch_eu_g.copy({"name": "21% EU G odd"})
        # One tax leg instead of the +100/−100 pair.
        for reps in (odd.invoice_repartition_line_ids,
                     odd.refund_repartition_line_ids):
            reps.filtered(lambda r: r.repartition_type == "tax"
                          and r.factor_percent < 0).unlink()
        self._status("2026-01-01", "identified")
        self.assertFalse(self.env["account.tax"].search([
            ("l10n_cz_vat_status_source_id", "=", odd.id)]))
        bill = self._move("in_invoice", "2026-03-10", partner=self.partner_de,
                          taxes=odd)
        self.assertTrue(bill.l10n_cz_vat_status_warning)
        with self.assertRaisesRegex(UserError, "no non-payer variant"):
            bill.action_post()
