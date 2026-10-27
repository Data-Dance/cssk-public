from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nCZPurchaseAdvanceWiring(TransactionCase):

    def test_a_company_whose_chart_comes_later_is_wired(self):
        """The hook only saw companies that had the chart at install time; a
        chart loaded afterwards (a new company, or one install run doing both)
        must be wired as it loads."""
        company = self.env["res.company"].create({
            "name": "Later", "country_id": self.env.ref("base.cz").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("cz", company, install_demo=False)
        clearing = company.advance_paid_clearing_account_id.with_company(company)
        self.assertEqual(clearing.code, "314001")
        self.assertTrue(clearing.reconcile)
        self.assertEqual(
            company.advance_paid_account_id.with_company(company).code, "314000")
        self.assertEqual(company.advance_purchase_journal_id.code, "PDADV")
        self.assertEqual(company.advance_purchase_journal_id.company_id, company)
