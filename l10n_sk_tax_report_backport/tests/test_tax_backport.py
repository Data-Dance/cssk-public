# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkTaxReportBackport(AccountTestInvoicingCommon):
    """The 19.0 SK VAT tax set + DPH tags must materialise on a fresh SK company."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def _tax(self, template):
        """The company's instance of an l10n_sk tax template, by XML-ID."""
        return self.env.ref(
            "account.%s_%s" % (self.company.id, template),
            raise_if_not_found=False,
        )

    def _tag_names(self, tax):
        return set(tax.repartition_line_ids.tag_ids.mapped("name"))

    def _fp(self, template):
        """The company's instance of a fiscal-position template, by XML-ID."""
        return self.env.ref(
            "account.%s_%s" % (self.company.id, template),
            raise_if_not_found=False,
        )

    def _fp_map(self, fp):
        """{src tax record -> dest tax record} for a fiscal position."""
        return {t.tax_src_id: t.tax_dest_id for t in fp.tax_ids}

    def test_backported_taxes_exist(self):
        """The taxes 18.0 core does NOT ship must exist after the backport."""
        for template in (
            "vs_rc_23", "vs_rc_19", "vs_rc_5",
            "vs_nad_eu_23", "vs_nad_eu_19", "vs_nad_eu_5",
            "vy_eu_m", "vy_eu_s", "vy_eu_t",
            "vy_mimo_eu",
            "vs_tri_23", "vs_imp_post_23", "vs_cust_23",
            "vy_bad_debt_23", "vs_unpaid_23", "vy_spec_reg_23",
            "vy_tuz_5", "vs_tuz_5", "vy_tuz_5_s", "vy_tuz_5_m",
            "vy_tuz_23_s", "vy_tuz_23_m",
        ):
            self.assertTrue(
                self._tax(template),
                "backported SK tax %s is missing on the chart" % template)

    def test_five_percent_rate_and_group(self):
        """The 5 % rate (absent from 18.0 core) and its tax group exist."""
        tax = self._tax("vy_tuz_5")
        self.assertEqual(tax.amount, 5.0)
        group = self.env.ref(
            "account.%s_tax_group_vat_5" % self.company.id,
            raise_if_not_found=False)
        self.assertTrue(group, "tax_group_vat_5 is missing")
        self.assertEqual(tax.tax_group_id, group)
        # 5 % sale carries the reduced-rate base/VAT tags 01a / 02a.
        self.assertLessEqual({"+01a", "+02a"}, self._tag_names(tax))

    def test_taxes_carry_report_tags(self):
        """Each key backported tax carries non-empty repartition tag_ids, with
        the expected DPH codes."""
        expected = {
            "vy_tuz_23": {"+03", "+04", "+24", "+25"},
            "vs_rc_23": {"+09b", "+19", "+10b", "+24_PR", "+28", "+25"},
            "vs_nad_eu_23": {"+07", "+19", "+08", "+24_PR", "+28", "+25"},
            "vy_eu_s": {"+14"},
            "vs_unpaid_23": {"+29"},
        }
        for template, codes in expected.items():
            tax = self._tax(template)
            self.assertTrue(tax, "%s missing" % template)
            names = self._tag_names(tax)
            self.assertTrue(names, "%s carries no repartition tags" % template)
            self.assertLessEqual(
                codes, names,
                "%s is missing DPH tags %s (has %s)"
                % (template, codes - names, sorted(names)))

    def test_dph_tags_created(self):
        """The DPH report tags exist as SK taxes-applicability account tags,
        resolvable by the evaluator's ``_get_tax_tags`` code lookup."""
        sk = self.env.ref("base.sk").id
        Tag = self.env["account.account.tag"]
        # (r17 is a *sum* aggregate in the DPH form, not a tag — so not listed.)
        for code in ("03", "04", "20", "21", "29", "01a", "24_PR"):
            tags = Tag._get_tax_tags(code, sk)
            self.assertTrue(
                tags, "DPH tag for code %s not resolvable" % code)

    def test_fiscal_position_substitutions(self):
        """The 19.0 fiscal-position tax swaps resolve on a fresh SK company.

        An EU-B2B (intra-community) customer's fiscal position must swap the
        domestic 23 % sale/purchase taxes to their EU counterparts, and the
        Export position must swap them to the 0 % export tax."""
        # EU intra-community B2B position.
        fp2 = self._fp("fiscal_position_template_2")
        self.assertTrue(fp2, "EU-intra fiscal position missing")
        m2 = self._fp_map(fp2)
        for src, dest in (
            ("vy_tuz_23", "vy_eu_m"),     # domestic goods -> EU supply
            ("vy_tuz_23_s", "vy_eu_s"),   # domestic services -> EU services
            ("vy_tuz_5", "vy_eu_m"),
            ("vs_tuz_23", "vs_nad_eu_23"),  # domestic purchase -> EU acquisition
            ("vs_tuz_19", "vs_nad_eu_19"),
            ("vs_tuz_5", "vs_nad_eu_5"),
        ):
            self.assertEqual(
                m2.get(self._tax(src)), self._tax(dest),
                "EU-intra position must map %s -> %s" % (src, dest))
        # The stale pre-19.0 dest taxes must NOT be referenced any more.
        dests = set(m2.values())
        self.assertNotIn(self._tax("vy_dod_eu"), dests)
        self.assertNotIn(self._tax("vs_nad_eu"), dests)

        # Export-outside-EU position (created by the backport; absent from 18.0).
        fp3 = self._fp("fiscal_position_template_3")
        self.assertTrue(fp3, "Export fiscal position was not created")
        m3 = self._fp_map(fp3)
        for src in ("vy_tuz_23", "vy_tuz_23_s", "vy_tuz_0"):
            self.assertEqual(
                m3.get(self._tax(src)), self._tax("vy_mimo_eu"),
                "Export position must map %s -> vy_mimo_eu" % src)

        # Domestic + EU-private positions disambiguate the generic rate to its
        # goods (_m) variant (19.0 does this via original_tax_ids on the _m tax).
        for fp_template in ("fiscal_position_template_1", "fp_intra_private"):
            m = self._fp_map(self._fp(fp_template))
            self.assertEqual(
                m.get(self._tax("vy_tuz_23")), self._tax("vy_tuz_23_m"),
                "%s must map vy_tuz_23 -> vy_tuz_23_m" % fp_template)

    def test_eu_taxes_legal_notes(self):
        """The three intra-EU sale taxes carry their invoice legal mention.

        18.0's ``invoice_legal_notes`` is not translatable, so the stored
        (English) base value is asserted."""
        for template, needle in (
            ("vy_eu_s", "Article 196"),
            ("vy_eu_m", "Article 138"),
            ("vy_eu_t", "Article 141"),
        ):
            tax = self._tax(template)
            self.assertTrue(tax, "%s missing" % template)
            self.assertTrue(
                tax.invoice_legal_notes and needle in tax.invoice_legal_notes,
                "%s is missing legal note %r (has %r)"
                % (template, needle, tax.invoice_legal_notes))
