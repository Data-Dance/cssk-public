# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestDppoPublished2026(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()
        # English regexes are a deliberate fixture language; production follows the user.
        self.env = self.env(context={**self.env.context, "lang": "en_US"})

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"

    def _make(self, year=2026):
        version = self.env.ref("l10n_sk_dppo.dppo_version_2026")
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": version.id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2026").id,
            "date_from": "%s-01-01" % year,
            "date_to": "%s-12-31" % year,
        })
        ret.action_compute_lines()
        return ret

    def _set(self, ret, **values):
        if "r920" in values:
            ret.l10n_sk_form_minimum_credit = True
        for code, value in values.items():
            line = ret.line_ids.filtered(lambda row: row.code == code)
            self.assertTrue(line, code)
            line.write({"is_overridden": True, "manual_value": value})
        ret.action_compute_lines()
        return {line.code: line.value for line in ret.line_ids}

    def test_published_layout_and_2027_period(self):
        ret = self._make(2027)
        codes = set(ret.line_ids.mapped("code"))
        self.assertTrue({"r306", "r309", "r310", "r315", "r1072"} <= codes)
        self.assertNotIn("r840", codes)
        derived = ret.version_id._cssk_derived_codes()
        self.assertIn("r315", derived)
        self.assertNotIn("r310", derived)
        self.assertFalse(ret._onchange_period_version())

    def test_new_adjustment_row_and_shifted_formula(self):
        ret = self._make()
        values = self._set(ret, r100=1000, r302=2, r303=3, r304=4,
                           r305=5, r306=6, r307=7, r308=8, r309=9,
                           r310=10, r320=20, r330=30, r560=40000)
        self.assertEqual(values["r310"], 10)
        self.assertEqual(values["r315"], 1038)
        self.assertEqual(values["r400"], 988)
        self.assertEqual(values["r600"], 98.8)

    def test_new_minimum_band_boundary(self):
        ret = self._make()
        values = self._set(ret, r100=0, r560=5000000)
        self.assertEqual(values["r810"], 3840)
        values = self._set(ret, r560=5000000.01)
        self.assertEqual(values["r810"], 11520)
        self.assertEqual(values["r1050"], 11520)

    def test_zero_turnover_is_not_automatically_exempt(self):
        ret = self._make()
        values = self._set(ret, r100=0, r560=0)
        self.assertEqual(values["r810"], 340)

    def test_minimum_new_band_is_period_start_sensitive(self):
        ret = self._make()
        ret.write({"date_from": "2025-07-01", "date_to": "2026-06-30"})
        values = self._set(ret, r100=0, r560=6000000)
        self.assertEqual(values["r810"], 3840)

    def test_first_period_reviewed_exemption_and_effective_overrides(self):
        ret = self._make(2027)
        values = self._set(ret, r100=1000, r560=40000, r810=0)
        self.assertEqual(values["r810"], 0)
        self.assertEqual(values["r1050"], 100)
        self.assertEqual(values["r900"], 0)
        # A later recomputation must clear the previously required minimum.
        values = self._set(ret, r810=340)
        self.assertEqual(values["r900"], 340)
        values = self._set(ret, r810=0)
        self.assertEqual(values["r900"], 0)
        self.assertEqual(values["r1050"], 100)

    def test_new_special_base_and_installment_settlement(self):
        ret = self._make()
        values = self._set(ret, r100=10000, r560=40000, r810=0,
                           r1060=100, r1070=200, r1071=300,
                           r1072=400, r1090=50, r1040=200)
        self.assertEqual(values["r1080"], 2000)
        self.assertEqual(values["r1100"], 1750)
        self.assertEqual(values["r1101"], 0)

    def test_minimum_credit_and_archive_vintage(self):
        ret = self._make()
        values = self._set(ret, r100=10000, r560=40000, r920=200)
        self.assertEqual(values["r1000"], 800)
        self.assertEqual(values["r1050"], 800)
        old = self.env.ref("l10n_sk_dppo.dppo_version_2025")
        self.assertEqual(str(old.valid_to), "2025-12-31")
        self.assertEqual(old.xml_schema_filename, "dppo2025_v2.xsd")
        self.assertIn("r840", old.line_def_ids.mapped("code"))

    def test_prior_credit_cannot_reduce_tax_below_current_minimum(self):
        ret = self._make()
        values = self._set(ret, r100=10000, r560=40000, r920=660)
        self.assertEqual(values["r1050"], 340)
        with self.assertRaisesRegex(UserError, "cannot exceed row 910"):
            self._set(ret, r920=660.01)

    def test_no_fabricated_official_wire(self):
        ret = self._make(2027)
        self.assertFalse(ret.version_id.xml_schema_data)
        with self.assertRaisesRegex(UserError, "official XML"):
            ret._cssk_preflight_export()
        with self.assertRaisesRegex(UserError, "official XML"):
            ret.action_export_xml()
        self.assertFalse(ret.xml_attachment_id)

    def test_api_cannot_export_2027_on_obsolete_2025_wire(self):
        ret = self._make(2027)
        ret.write({
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2025").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id})
        ret.action_compute_lines()
        with self.assertRaisesRegex(UserError, "does not cover"):
            ret.action_export_xml()
        self.assertFalse(ret.xml_attachment_id)

    def test_fiscal_period_overlap_does_not_authorize_obsolete_wire(self):
        ret = self._make(2026)
        ret.write({
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2025").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id,
            "date_from": "2025-12-01", "date_to": "2026-11-30"})
        ret.action_compute_lines()
        with self.assertRaisesRegex(UserError, "filing deadline"):
            ret.action_export_xml()

    def test_fiscal_deadline_extension_changes_form_not_minimum_start(self):
        ret = self._make(2026)
        old = self.env.ref("l10n_sk_dppo.dppo_version_2025")
        current = ret.version_id
        ret.write({"date_from": "2025-07-01", "date_to": "2026-06-30",
                   "version_id": old.id,
                   "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id})
        ret.action_compute_lines()
        self.assertFalse(ret._l10n_sk_dppo_requires_2026_form())
        self.assertEqual(ret.l10n_sk_dppo_applicable_version_ids, old)
        ret._cssk_preflight_export()
        ret.action_export_xml()
        old_attachment = ret.xml_attachment_id
        old_bytes = old_attachment.raw
        ret.action_reset_to_draft()
        ret.write({"l10n_sk_dppo_filing_deadline": "2027-03-31"})
        self.assertEqual(ret.l10n_sk_dppo_applicable_version_ids, current)
        with self.assertRaisesRegex(UserError, "filing deadline"):
            ret._cssk_preflight_export()
        ret.write({"version_id": current.id,
                   "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2026").id})
        values = self._set(ret, r560=6000000)
        ret._l10n_sk_dppo_check_form_applicability()
        self.assertEqual(values["r810"], 3840)
        self.assertEqual(old_attachment.raw, old_bytes)
        with self.assertRaisesRegex(UserError, "official XML"):
            ret._cssk_preflight_export()

    def test_new_form_rejects_pre_2027_deadline(self):
        ret = self._make(2026)
        ret.write({"date_from": "2025-07-01", "date_to": "2026-06-30"})
        with self.assertRaisesRegex(UserError, "filing deadline"):
            ret._l10n_sk_dppo_check_form_applicability()

    def test_late_filing_date_is_not_the_legal_deadline(self):
        ret = self._make(2026)
        ret.write({
            "date_from": "2025-01-01", "date_to": "2025-12-31",
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2025").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id,
            "submitted_date": "2027-05-15"})
        self.assertFalse(ret._l10n_sk_dppo_requires_2026_form())
        ret._l10n_sk_dppo_check_form_applicability()

    def test_2027_posted_ledger_to_native_provision(self):
        Account = self.env["account.account"]

        def account(prefix, kind):
            found = Account.search([
                ("code", "=like", prefix + "%"),
                ("company_ids", "in", self.company.id)], limit=1)
            return found or Account.create({
                "name": prefix, "code": prefix + "000", "account_type": kind,
                "company_ids": [Command.set([self.company.id])]})

        income = account("602", "income")
        bank = account("221", "asset_cash")
        expense = account("591", "expense")
        payable = account("341", "liability_current")
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2027-01-15",
            "journal_id": self.company_data["default_journal_misc"].id,
            "line_ids": [
                Command.create({"account_id": income.id, "credit": 1000}),
                Command.create({"account_id": bank.id, "debit": 1000}),
            ]})
        move.action_post()
        ret = self._make(2027)
        values = self._set(ret, r810=0)
        self.assertEqual(values["r100"], 1000)
        self.assertEqual(values["r560"], 1000)
        self.assertEqual(values["r1050"], 100)
        ret.action_post_provision()
        provision = ret.provision_move_id
        self.assertEqual(provision.state, "posted")
        self.assertEqual(str(provision.date), "2027-12-31")
        self.assertEqual(provision.line_ids.filtered(
            lambda row: row.account_id == expense).debit, 100)
        self.assertEqual(provision.line_ids.filtered(
            lambda row: row.account_id == payable).credit, 100)
        with self.assertRaises(UserError):
            ret.action_post_provision()
        ret.action_compute_lines()
        self.assertEqual(ret.line_ids.filtered(lambda row: row.code == "r100").value, 1000)
        self.assertEqual(ret.provision_move_id, provision)

    def test_exempt_tax_fully_consumed_by_prior_credit(self):
        ret = self._make()
        ret.l10n_sk_form_minimum_exemption = True
        values = self._set(ret, r800=10759.26, r810=0,
                           r920=10759.26, r1090=3000)
        for code in ("r1000", "r1050", "r1100"):
            self.assertEqual(values[code], 0, code)
        self.assertEqual(values["r1101"], -3000)

    def test_empty_table_k_does_not_fill_conditional_rows(self):
        ret = self._make()
        values = self._set(ret, r800=10759.26, r810=960)
        for code in ("r910", "r920", "r1000"):
            self.assertEqual(values[code], 0, code)
        self.assertEqual(values["r1050"], 10759.26)

    def test_filled_zero_credit_preserves_tax(self):
        ret = self._make()
        values = self._set(ret, r800=10759.26, r810=960, r920=0)
        self.assertEqual(values["r910"], 9799.26)
        self.assertEqual(values["r1000"], 10759.26)
        self.assertEqual(values["r1050"], 10759.26)

    def test_short_2026_deadline_selects_legacy_form(self):
        ret = self._make()
        ret.write({"date_from": "2026-01-01", "date_to": "2026-09-30"})
        old = self.env.ref("l10n_sk_dppo.dppo_version_2025")
        self.assertEqual(ret.l10n_sk_dppo_applicable_version_ids, old)
        self.assertFalse(ret._onchange_period_version())
        ret.version_id = old
        self.assertTrue(ret._cssk_preflight_export())
        ret.l10n_sk_dppo_filing_deadline = "2027-03-31"
        self.assertEqual(ret.l10n_sk_dppo_applicable_version_ids,
                         self.env.ref("l10n_sk_dppo.dppo_version_2026"))
        with self.assertRaises(UserError):
            ret._cssk_preflight_export()

    def test_short_deadline_refuses_an_older_legacy_edition(self):
        ret = self._make()
        ret.write({"date_from": "2026-01-01", "date_to": "2026-09-30",
                   "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2024").id})
        with self.assertRaises(UserError):
            ret._cssk_preflight_export()

    def test_nonzero_credit_requires_table_k_declaration(self):
        ret = self._make()
        row = ret.line_ids.filtered(lambda line: line.code == "r920")
        row.write({"is_overridden": True, "manual_value": 1})
        with self.assertRaisesRegex(UserError, "Table K"):
            ret.action_compute_lines()

    def test_zero_current_claim_keeps_minimum_at_and_below_boundary(self):
        for profit, tax in ((-1000, 0), (0, 0), (1000, 100), (3400, 340), (3400.1, 340.01)):
            for declared in (False, True):
                with self.subTest(profit=profit, declared=declared):
                    ret = self._make()
                    values = self._set(ret, r100=profit, r560=10000, r810=340)
                    ret.l10n_sk_form_minimum_credit = declared
                    ret.action_compute_lines()
                    values = {line.code: line.value for line in ret.line_ids}
                    self.assertEqual(values["r800"], tax)
                    self.assertEqual(values["r1050"], max(340, tax))
                    self.assertEqual(values["r1110"], tax)
                    self.assertEqual(values["r1000"], tax if declared else 0)
