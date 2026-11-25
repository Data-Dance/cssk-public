# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Slovak cross-checks are for Slovak filings.

The three forms are shared with the Czech suite, and a database can hold a
Slovak and a Czech company. The buttons used to show on every filing and
would compare a Czech one with the Slovak row map.
"""

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged

BUTTONS = (
    ("cssk.control.statement", "action_reconcile_dph"),
    ("cssk.ec.summary.statement", "action_reconcile_dph"),
    ("cssk.vat.return", "action_reconcile_books"),
)


@tagged("post_install", "-at_install")
class TestButtonsByCountry(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.company_data["company"]

    def test_each_button_is_hidden_off_slovak_filings(self):
        for model, method in BUTTONS:
            arch = etree.fromstring(
                self.env[model].get_view(view_type="form")["arch"])
            button = arch.xpath("//button[@name='%s']" % method)
            self.assertEqual(len(button), 1, (model, method))
            self.assertIn("!= 'SK'", button[0].get("invisible"), model)

    def test_the_actions_refuse_another_country_s_filing(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref(
                "l10n_sk_vat_return.dph_version_2025").id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month"})
        ret.action_reconcile_books()        # Slovak: runs
        self.company.account_fiscal_country_id = self.env.ref("base.cz")
        self.assertEqual(ret.country_id.code, "CZ")
        with self.assertRaisesRegex(UserError, "Slovak filings"):
            ret.action_reconcile_books()
