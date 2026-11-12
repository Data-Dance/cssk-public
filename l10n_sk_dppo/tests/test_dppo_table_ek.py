# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from io import BytesIO

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools.pdf import PdfReader

from .test_dppo_pdf import TestDppoOfficialPdf


@tagged("post_install", "-at_install")
class TestDppoCreditAnnexes(AccountTestInvoicingCommon):
    # Share fixtures, not the inherited test suite.
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write(
            {
                "name": "Synthetic tax-credit company",
                "l10n_sk_dic": "2020317068",
                "company_registry": "36000001",
                "street": "Hlavná 12",
                "city": "Bratislava",
                "zip": "81101",
                "country_id": cls.env.ref("base.sk").id,
                "phone": "+421905111222",
                "email": "test@example.invalid",
            }
        )
        cls.person = cls.env["res.partner"].create(
            {
                "name": "Jana Test",
                "street": "Dlhá 8",
                "city": "Bratislava",
                "zip": "81101",
                "country_id": cls.env.ref("base.sk").id,
                "company_id": cls.company.id,
                "phone": "+421905222333",
                "email": "person@example.invalid",
            }
        )

    _make = TestDppoOfficialPdf._make
    _set = TestDppoOfficialPdf._set

    def _return(self):
        ret = self._make()
        self._set(ret, r100=10000, r560=10000, r810=340, a06=0, b01=0, b02=0)
        ret.l10n_sk_form_minimum_exemption = False
        return ret

    def _e(self, ret, **values):
        return self.env["l10n.sk.dppo.table.e.line"].create(
            {
                "return_id": ret.id,
                "country_id": self.env.ref("base.cz").id,
                "foreign_base": 2500,
                "eligible_tax": 200,
                "source_tax": 200,
                "tax_currency_id": self.env.ref("base.EUR").id,
                "paid_on": "2028-02-01",
                "evidence": "Reviewed synthetic foreign income, treaty and paid tax certificate",
                **values,
            }
        )

    def _k(self, ret, **values):
        return self.env["l10n.sk.dppo.table.k.line"].create(
            {
                "return_id": ret.id,
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "minimum_tax": 960,
                "credit_amount": 600,
                "prior_claimed": 100,
                "claimed": 400,
                "subsequent_period_number": "2",
                "paid_amount": 960,
                "paid_on": "2026-03-01",
                "evidence": "Filed synthetic return, paid minimum tax and reviewed prior credit history",
                **values,
            }
        )

    def test_combined_credit_tax_spine_and_pdf(self):
        ret = self._return()
        self._e(ret)
        self._k(ret)
        ret.action_apply_table_ek_credits()
        values = {line.code: line.value for line in ret.line_ids}
        self.assertEqual(
            [values[key] for key in ("r710", "r800", "r910", "r920", "r1050")],
            [200, 800, 460, 400, 400],
        )
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertEqual(
            data["table_e"]["rows"], [10000, 2500, 25, 250, 0, 0, 0, 200, 250, 200]
        )
        self.assertEqual(data["table_k"]["items"][0]["remaining"], 100)
        pdf = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        self.assertEqual(len(pdf.pages), 21)
        self.assertIn("CZ", pdf.pages[14].extract_text())

    def test_zero_claim_preserves_k_evidence(self):
        ret = self._return()
        self._k(ret, claimed=0)
        ret.action_apply_table_ek_credits()
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertFalse(ret.l10n_sk_form_minimum_credit)
        self.assertNotIn("r920", data["rows"])
        self.assertEqual(data["table_k"]["items"][0]["remaining"], 500)
        self.assertIn(
            "6",
            PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
            .pages[9]
            .extract_text(),
        )

    def test_k_five_digit_source_fits_continuous_field(self):
        ret = self._return()
        self._k(
            ret,
            minimum_tax=11520,
            credit_amount=11520,
            paid_amount=11520,
            prior_claimed=0,
            claimed=0,
        )
        ret.action_apply_table_ek_credits()
        pdf = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        self.assertEqual(len(pdf.pages), 21)
        # The whole-euro rectangle is continuous. Preserve all five digits;
        # retain cents in their original two printed cells.
        self.assertGreaterEqual(pdf.pages[9].extract_text().count("11520"), 3)

    def test_k_five_digit_total_preserves_individual_sources(self):
        ret = self._return()
        self._k(
            ret,
            minimum_tax=9600,
            credit_amount=9000,
            paid_amount=9600,
            prior_claimed=0,
            claimed=0,
        )
        self._k(
            ret,
            date_from="2026-01-01",
            date_to="2026-12-31",
            minimum_tax=9600,
            credit_amount=9000,
            paid_amount=9600,
            prior_claimed=0,
            claimed=0,
            subsequent_period_number="1",
        )
        ret.action_apply_table_ek_credits()
        pdf = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        text = pdf.pages[9].extract_text()
        self.assertIn("18000", text)
        self.assertGreaterEqual(text.count("9000"), 4)

    def test_hybrid_caps_and_fx(self):
        ret = self._return()
        line = self._e(
            ret,
            foreign_base=2000,
            hybrid_base=1000,
            eligible_tax=350,
            source_tax=8750,
            tax_currency_id=self.env.ref("base.CZK").id,
            eur_rate=0.04,
            fx_evidence="Reviewed section 31 source exchange rate",
        )
        ret.action_apply_table_ek_credits()
        data = ret._l10n_sk_dppo_pdf_payload()
        self.assertEqual(
            data["table_e"]["rows"],
            [10000, 2000, 20, 200, 1000, 10, 100, 350, 300, 300],
        )
        self.assertIn("8750.00", data["notes"])
        line.eligible_tax = 351
        with self.assertRaisesRegex(UserError, "converted source"):
            ret.action_apply_table_ek_credits()

    def test_lawful_estimate_different_tax_period(self):
        ret = self._return()
        line = self._e(
            ret,
            tax_status="estimated",
            paid_on=False,
            foreign_date_from="2026-07-01",
            foreign_date_to="2027-06-30",
        )
        ret.action_apply_table_ek_credits()
        line.write({"foreign_date_from": "2027-01-01", "foreign_date_to": "2027-12-31"})
        with self.assertRaisesRegex(UserError, "different"):
            ret._l10n_sk_dppo_pdf_payload()

    def test_excess_combined_claim_rolls_back(self):
        ret = self._return()
        self._e(ret)
        self._k(ret, claimed=500)
        before = [(line.code, line.value, line.manual_value) for line in ret.line_ids]
        with self.assertRaisesRegex(UserError, "above the current minimum"):
            ret.action_apply_table_ek_credits()
        self.assertEqual(
            before,
            [(line.code, line.value, line.manual_value) for line in ret.line_ids],
        )

    def test_third_tax_period_expiry_including_short_periods(self):
        ret = self._return()
        ret.write({"date_from": "2026-09-01", "date_to": "2026-12-31"})
        # Three subsequent short tax periods are possible without three calendar years.
        line = self._k(
            ret,
            date_from="2026-01-01",
            date_to="2026-02-28",
            subsequent_period_number="3",
            claimed=0,
        )
        data = line._form_payload()
        self.assertEqual(data["expired"], 500)
        self.assertEqual(data["remaining"], 0)

    def test_unpaid_and_duplicate_prior_periods_rejected(self):
        ret = self._return()
        line = self._k(ret, paid_amount=959)
        with self.assertRaisesRegex(UserError, "fully paid"):
            ret.action_apply_table_ek_credits()
        line.paid_amount = 960
        self._k(ret, claimed=0)
        with self.assertRaisesRegex(UserError, "overlap"):
            ret.action_apply_table_ek_credits()

    def test_first_following_period_has_no_prior_usage(self):
        ret = self._return()
        line = self._k(ret, date_from="2026-01-01", date_to="2026-12-31")
        with self.assertRaisesRegex(UserError, "subsequent tax period"):
            line._form_payload()
        line.subsequent_period_number = "1"
        with self.assertRaisesRegex(UserError, "subsequent tax period"):
            line._form_payload()
        line.prior_claimed = 0
        self.assertEqual(line._form_payload()["remaining"], 200)

    def test_missing_and_stale_inputs_block_export(self):
        ret = self._return()
        self._set(ret, r710=200)
        with self.assertRaisesRegex(UserError, "Tables E/K"):
            ret._l10n_sk_dppo_pdf_payload()
        line = self._e(ret)
        ret.action_apply_table_ek_credits()
        original = ret._l10n_sk_dppo_official_pdf()
        line.eligible_tax = 100
        with self.assertRaisesRegex(UserError, "Tables E/K"):
            ret._l10n_sk_dppo_pdf_payload()
        ret.action_apply_table_ek_credits()
        self.assertNotEqual(original, ret._l10n_sk_dppo_official_pdf())

    def test_credit_input_acl_and_final_state_guard(self):
        ret = self._return()
        line = self._e(ret)
        outsider = new_test_user(
            self.env, login="credit_outsider", groups="base.group_user"
        )
        with self.assertRaises(AccessError):
            line.with_user(outsider).write({"eligible_tax": 1})
        ret.write({"state": "exported"})
        with self.assertRaises(UserError):
            line.write({"eligible_tax": 1})
        with self.assertRaises(UserError):
            line.unlink()

    def test_long_country_and_conversion_evidence_kept(self):
        ret = self._return()
        self._e(
            ret,
            tax_currency_id=self.env.ref("base.CZK").id,
            source_tax=5000,
            eur_rate=0.04,
            fx_evidence=" ".join("ReviewedRate%s" % index for index in range(160)),
        )
        ret.action_apply_table_ek_credits()
        pdf = PdfReader(BytesIO(ret._l10n_sk_dppo_official_pdf()))
        self.assertGreater(len(pdf.pages), 21)
        self.assertIn(
            "ReviewedRate159", " ".join(page.extract_text() for page in pdf.pages)
        )
