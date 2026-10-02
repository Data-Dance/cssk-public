# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNaceCode(TransactionCase):

    def test_the_code_is_kept_as_digits(self):
        partner = self.env["res.partner"].create({"name": "A", "nace_code": "62.01"})
        self.assertEqual(partner.nace_code, "6201")
        partner.nace_code = "35 11 0"
        self.assertEqual(partner.nace_code, "35110")

    def test_a_code_is_two_to_six_digits(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create({"name": "B", "nace_code": "1"})
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create({"name": "C", "nace_code": "1234567"})

    def test_contacts_share_the_company_s_activity(self):
        company = self.env["res.partner"].create({
            "name": "Firma s.r.o.", "is_company": True, "nace_code": "62090"})
        contact = self.env["res.partner"].create({"name": "Jana", "parent_id": company.id})
        self.assertEqual(contact.nace_code, "62090")

    def test_the_company_reads_its_partner(self):
        self.env.company.nace_code = "35110"
        self.assertEqual(self.env.company.partner_id.nace_code, "35110")
