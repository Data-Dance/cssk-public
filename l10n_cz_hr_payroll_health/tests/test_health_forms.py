# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The company's default insurer and payer number decide what the health
filings carry, so they must be editable on the company form."""

from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHealthForms(TransactionCase):
    def _form_fields(self, model):
        arch = self.env[model].get_views([(False, "form")])[
            "views"]["form"]["arch"]
        return {n.get("name") for n in etree.fromstring(arch).iter("field")}

    def test_company_form_carries_health_defaults(self):
        names = self._form_fields("res.company")
        self.assertIn("l10n_cz_health_insurer_code", names)
        self.assertIn("l10n_cz_health_payer_number", names)

    def test_employee_form_carries_insurer(self):
        self.assertIn("l10n_cz_health_insurer_code",
                      self._form_fields("hr.employee"))
