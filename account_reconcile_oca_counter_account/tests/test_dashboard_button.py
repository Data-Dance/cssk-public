# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDashboardButton(TransactionCase):
    def test_the_count_needs_no_plural_agreement(self):
        """"Reconcile N Items" cannot be translated into Slovak or Czech: the
        noun has to agree with N. The button reads "N to reconcile"."""
        arch = self.env["account.journal"].get_views(
            [(self.env.ref("account.account_journal_dashboard_kanban_view").id, "kanban")]
        )["views"]["kanban"]["arch"]
        self.assertIn("to reconcile", arch)
        self.assertNotIn(" Items</button>", arch)

    def test_slovak_and_czech(self):
        for lang, text in (("sk_SK", "na párovanie"), ("cs_CZ", "ke spárování")):
            if not self.env["res.lang"]._lang_get(lang):
                continue
            arch = self.env["account.journal"].with_context(lang=lang).get_views(
                [(self.env.ref("account.account_journal_dashboard_kanban_view").id, "kanban")]
            )["views"]["kanban"]["arch"]
            self.assertIn(text, arch, lang)
