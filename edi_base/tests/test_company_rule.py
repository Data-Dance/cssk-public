# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEdiMessageCompanyRule(TransactionCase):
    def test_messages_are_confined_to_the_users_companies(self):
        rule = self.env.ref("edi_base.rule_edi_message_company")
        self.assertTrue(rule["global"])
        self.assertEqual(rule.model_id.model, "edi.message")
        self.assertIn("company_ids", rule.domain_force)
