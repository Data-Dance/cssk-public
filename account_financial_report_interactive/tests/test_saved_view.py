# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSavedView(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.View = cls.env["account.financial.report.interactive.view"]
        cls.data = {"company_id": cls.company.id, "date_from": "2026-03-01", "date_to": "2026-03-31",
                    "only_posted_moves": True, "account_ids": [], "partner_ids": [], "journal_ids": []}
        cls.other = cls.env["res.users"].create({
            "name": "Other accountant", "login": "other_accountant",
            "group_ids": [(6, 0, [cls.env.ref("account.group_account_user").id])],
            "company_id": cls.company.id, "company_ids": [(6, 0, cls.company.ids)]})

    def _save(self, **values):
        return self.View.browse(self.View.save_view(dict({"name": "March", "data": self.data}, **values)))

    def test_relative_periods(self):
        view = self._save(period="this_month")
        self.assertEqual(view._period_dates(date(2026, 5, 17))[:2], (date(2026, 5, 1), date(2026, 5, 31)))
        view.period = "last_quarter"
        self.assertEqual(view._period_dates(date(2026, 5, 17))[:2], (date(2026, 1, 1), date(2026, 3, 31)))
        view.period = "this_year"
        self.assertEqual(view._period_dates(date(2026, 5, 17))[:2], (date(2026, 1, 1), date(2026, 12, 31)))
        view.period = "last_month"
        self.assertEqual(view._period_dates(date(2026, 1, 10))[:2], (date(2025, 12, 1), date(2025, 12, 31)))
        view.period = "fixed"
        self.assertEqual(view._resolved_data()["date_from"], "2026-03-01")

    def test_open_carries_filters_and_comparison(self):
        view = self._save(comparison={"mode": "previous", "count": 3},
                          data=dict(self.data, extra_domain="[('partner_id', '!=', False)]"))
        action = view.action_open()
        self.assertEqual(action["tag"], "afr_interactive_ledger")
        self.assertEqual(action["params"]["comparison"], {"mode": "previous", "count": 3})
        self.assertEqual(action["params"]["data"]["extra_domain"], "[('partner_id', '!=', False)]")

    def test_private_and_shared(self):
        mine = self._save(name="Mine")
        shared = self._save(name="Ours", shared=True)
        names = {v["name"] for v in self.View.with_user(self.other).list_views()}
        self.assertEqual(names, {"Ours"})
        with self.assertRaises(AccessError):
            shared.with_user(self.other).write({"name": "Hijacked"})
        with self.assertRaises(AccessError):
            mine.with_user(self.other).read(["name"])

    def test_one_default_per_user_and_the_menu(self):
        first = self._save(name="First", is_default=True)
        second = self._save(name="Second", is_default=True)
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)
        self.assertEqual(self.View.action_open_default()["params"]["view_id"], second.id)
        # Without a default: a trial balance of the current fiscal year.
        fallback = self.View.with_user(self.other).action_open_default()
        self.assertNotIn("view_id", fallback["params"])
        self.assertTrue(fallback["params"]["data"]["hide_account_at_0"])
