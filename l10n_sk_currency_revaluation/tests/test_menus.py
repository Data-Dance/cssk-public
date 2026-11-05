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


@tagged("post_install", "-at_install")
class TestRevaluationAccess(TransactionCase):

    def test_the_accountant_role_sees_the_revaluation_menus(self):
        """The OCA menus are limited to group_revaluation_additional; the
        accountant role must include it, for new and existing members alike."""
        manager = self.env.ref("account.group_account_manager")
        reval = self.env.ref("account_multicurrency_revaluation.group_revaluation_additional")
        self.assertIn(reval, manager.all_implied_ids)
        user = self.env["res.users"].create({
            "name": "Reval Accountant", "login": "reval_accountant",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id, manager.id])],
        })
        self.assertTrue(user.has_group(
            "account_multicurrency_revaluation.group_revaluation_additional"))
        visible = self.env["ir.ui.menu"].with_user(user)._visible_menu_ids()
        menu = self.env.ref(
            "account_multicurrency_revaluation.menu_view_account_currency_revaluation_wizard")
        self.assertIn(menu.id, visible)

    def test_a_bookkeeper_does_not(self):
        user = self.env["res.users"].create({
            "name": "Reval Bookkeeper", "login": "reval_bookkeeper",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id,
                                  self.env.ref("account.group_account_user").id])],
        })
        self.assertFalse(user.has_group(
            "account_multicurrency_revaluation.group_revaluation_additional"))
