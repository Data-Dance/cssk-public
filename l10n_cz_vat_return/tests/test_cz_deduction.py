# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzSelfAssessedDeduction(AccountTestInvoicingCommon):
    """ř43/ř44 — the deduction of tax self-assessed on ř3–13.

    ``l10n_cz`` tags only the DECLARATION of a self-assessed purchase and
    leaves the −100 leg bare, so the deduction reaches no line of the return.
    Measured against 59 filed Řádné returns, 2021-07 .. 2026-05: ř43 and ř44
    computed 0.00 in **every** period against filed figures totalling 94.5M of
    base and 14 534 001.54 of tax, while the output side of the same returns
    agreed to within 0.03 %.
    """

    chart_template = "cz"

    def _names(self, reps):
        return set(reps.tag_ids.mapped("name"))

    def test_every_self_assessed_purchase_tax_tags_its_deduction(self):
        """Asserted over the WHOLE chart, because the defect was uniform.

        45 self-assessed purchase taxes and every one of them affected, which
        is what makes it a chart-level gap rather than a mapping mistake — and
        why one tax passing would prove nothing.
        """
        company = self.env.company
        company._cz_tag_selfassessed_deduction()
        taxes = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", company.id), ("type_tax_use", "=", "purchase"),
        ])
        checked, missing = 0, []
        for tax in taxes:
            reps = tax.invoice_repartition_line_ids
            legs = reps.filtered(lambda r: r.repartition_type == "tax")
            if len(legs) < 2:
                continue  # not self-assessed: nothing to deduct
            base = reps.filtered(lambda r: r.repartition_type == "base")
            if not ({"VAT 43 Base", "VAT 44 Base"} & self._names(base)):
                continue  # declares on no line this maps from
            checked += 1
            deduction = legs.filtered(lambda r: r.factor_percent < 0)
            if not ({"VAT 43 Total", "VAT 44 Total"} & self._names(deduction)):
                missing.append(tax.name)
        self.assertTrue(checked, "no self-assessed purchase tax was examined")
        self.assertFalse(
            missing,
            "self-assessed purchase taxes whose deduction reaches no line of "
            "the return: %s" % (missing,))

    def test_the_band_comes_from_the_declaration_not_the_rate(self):
        """ř43 is základní and ř44 snížená, and the tax already says which.

        Derived from the declaration tag (ř3/ř5/ř7/ř10/ř12 against
        ř4/ř6/ř8/ř11/ř13)
        rather than from a rate literal, so a chart that adds a rate needs no
        change here. Asserting it stops someone 'simplifying' it into a list of
        rates, which is the version that breaks silently.
        """
        company = self.env.company
        company._cz_tag_selfassessed_deduction()
        taxes = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", company.id), ("type_tax_use", "=", "purchase"),
        ])
        for tax in taxes:
            names = self._names(tax.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base"))
            if "VAT 43 Base" in names:
                self.assertTrue(
                    names & {"VAT 3 Base", "VAT 5 Base", "VAT 7 Base",
                             "VAT 10 Base", "VAT 12 Base"},
                    "%s claims the základní deduction without declaring on a "
                    "základní line" % tax.name)
            if "VAT 44 Base" in names:
                self.assertTrue(
                    names & {"VAT 4 Base", "VAT 6 Base", "VAT 8 Base",
                             "VAT 11 Base", "VAT 13 Base"},
                    "%s claims the snížená deduction without declaring on a "
                    "snížená line" % tax.name)

    def test_the_line_definitions_collect_those_tags_with_the_right_sign(self):
        """Tagging the repartition is half of it; the form must read them.

        ⚠️ The two TAX lines NEGATE and the two BASE lines do not. A
        self-assessed tax deducts on the −100 repartition leg, so its balance
        is a credit and reads negative, while ř40/ř41 collect an ordinary
        purchase deduction on +100 and read positive. Measured on the filed
        returns after the tags landed: −8 956 925.28 against a filed
        8 688 149.60, magnitude right and sign inverted.
        """
        version = self.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        formulas = {d.code: (d.kind, d.tag_formula) for d in version.line_def_ids}
        for code, tag in (("nar_zdp23", "VAT 43 Base"),
                          ("od_zdp23", "-VAT 43 Total"),
                          ("nar_zdp5", "VAT 44 Base"),
                          ("od_zdp5", "-VAT 44 Total")):
            self.assertEqual(
                formulas.get(code), ("tags", tag),
                "%s must collect %s — it was 'manual' because the chart "
                "defined no such tag" % (code, tag))
        # krácený odpočet stays manual: a partial claim is the taxpayer's
        # coefficient, not a property of the tax.
        for code in ("odkr_zdp23", "odkr_zdp5"):
            self.assertEqual(formulas.get(code, ("", ""))[0], "manual")

    def test_running_it_twice_adds_nothing(self):
        """It runs on install, on chart load and from a migration."""
        company = self.env.company
        company._cz_tag_selfassessed_deduction()
        self.assertEqual(
            company._cz_tag_selfassessed_deduction(), 0,
            "a second run must report no change")

    def test_import_of_goods_is_not_charged_to_the_supplier(self):
        """ř. 7/8 arrives with ONE leg, and one leg is a wrong payable.

        Self-assessed VAT is not charged by the supplier — you owe the state,
        not the vendor — so the two legs must cancel on the document. Measured
        on the shipped Czech chart with a 1 000 CZK bill before the hook runs:

            21% EU G   untaxed 1000.00  tax   0.00  TOTAL 1000.00
            21% EX G   untaxed 1000.00  tax 210.00  TOTAL 1210.00

        The second asks the user to pay 1 210 against a 1 000 invoice. It also
        leaves the move unbalanced, so Odoo adds an automatic balancing line
        and posts anyway — on a real agenda that put 912.87 onto 261000
        *Peníze na cestě*, an account the document never touched.
        """
        company = self.env.company
        tax = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", company.id), ("name", "=", "21% EX G"),
        ], limit=1)
        self.assertTrue(tax, "the Czech chart should ship an import-of-goods tax")
        legs = tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax")
        self.assertEqual(
            len(legs), 2,
            "an import of goods self-assesses, so its tax must cancel on the "
            "document rather than be charged to the supplier")
        self.assertEqual(
            sum(legs.mapped("factor_percent")), 0.0,
            "the two legs must sum to zero or the bill total is inflated by "
            "the rate")
        self.assertIn(
            "VAT 43 Total", self._names(legs.filtered(
                lambda r: r.factor_percent < 0)),
            "the leg carries the ř43 deduction")
        self.assertIn("VAT 43 Base", self._names(
            tax.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base")))

    def test_a_new_means_of_transport_is_left_alone(self):
        """ř. 9 is the row this deliberately does NOT repair.

        Rows 3–13 are all deductible on ř43/44 by the caption's own wording,
        but ř. 9 is *pořízení nového dopravního prostředku*, where the
        deduction is not automatic. Its single leg may well be intended, and
        nothing here has the evidence to overrule it — so a change that
        silently swept it up with the import rows would be making a tax
        decision nobody asked for.
        """
        company = self.env.company
        tax = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", company.id), ("name", "=", "21% Vehicle"),
        ], limit=1)
        if not tax:
            self.skipTest("this chart ships no ř. 9 tax")
        legs = tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax")
        self.assertEqual(
            len(legs), 1,
            "ř. 9 must keep the shape the localization gave it")
        self.assertNotIn("VAT 43 Base", self._names(
            tax.invoice_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base")))
