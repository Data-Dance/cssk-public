# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestClosingMenu(TransactionCase):

    def test_one_closing_menu(self):
        closing = self.env.ref("account.account_closing_menu")
        for xmlid in ("account_multicurrency_revaluation.menu_view_account_currency_revaluation_wizard",
                      "account_multicurrency_revaluation.menu_view_reverse_account_currency_revaluation_wizard"):
            self.assertEqual(self.env.ref(xmlid).parent_id, closing, xmlid)
        duplicate = self.env.ref(
            "account_multicurrency_revaluation.menu_view_account_currency_revaluation_closing")
        self.assertFalse(duplicate.active)
        # only one "Closing" left under Accounting → Accounting
        siblings = self.env["ir.ui.menu"].search([("parent_id", "=", closing.parent_id.id)])
        self.assertEqual(len(siblings.filtered(lambda m: m.with_context(lang="en_US").name == "Closing")), 1)
