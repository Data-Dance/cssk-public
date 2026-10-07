# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkDic(TransactionCase):
    """DIČ is a Slovak identifier distinct from both IČO and IČ DPH."""

    def test_a_subject_can_hold_a_dic_without_being_a_vat_payer(self):
        """The whole reason the field exists: registered for income tax,
        not registered for VAT."""
        partner = self.env["res.partner"].create(
            {"name": "Neplatiteľ s.r.o.", "company_registry": "31333532",
             "l10n_sk_dic": "2020317068"}
        )
        self.assertEqual(partner.l10n_sk_dic, "2020317068")
        self.assertFalse(partner.vat)

    def test_the_company_field_is_the_partner_field(self):
        company = self.env["res.company"].create({"name": "Testovacia s.r.o."})
        company.l10n_sk_dic = "2020317068"
        self.assertEqual(company.partner_id.l10n_sk_dic, "2020317068")
        company.partner_id.l10n_sk_dic = "1111111111"
        self.assertEqual(company.l10n_sk_dic, "1111111111")

    def test_the_legacy_field_is_gone_from_the_shared_base(self):
        """It lived in l10n_cssk_core on the premise that Czech needed it too.
        Czech DIČ *is* the VAT number, so it did not."""
        self.assertNotIn("l10n_cssk_dic", self.env["res.partner"]._fields)

    def test_income_tax_id_is_the_same_value(self):
        """l10n_sk's own company field now reads the partner's DIČ.

        Two company fields for one number is only safe while neither can hold
        a number of its own — so assert they move together in both directions.
        """
        company = self.env["res.company"].create({"name": "Dvojpole s.r.o."})
        company.l10n_sk_dic = "2020317068"
        self.assertEqual(company.income_tax_id, "2020317068")
        company.income_tax_id = "1111111111"
        self.assertEqual(company.l10n_sk_dic, "1111111111")
        self.assertEqual(company.partner_id.l10n_sk_dic, "1111111111")

    def test_a_contact_inherits_the_company_dic(self):
        """The DIČ is a commercial field: a child contact files nothing of its
        own, so the number that reaches a document is the parent's."""
        parent = self.env["res.partner"].create(
            {"name": "Materská s.r.o.", "is_company": True,
             "l10n_sk_dic": "2020317068"}
        )
        child = self.env["res.partner"].create(
            {"name": "Jozef Mrkvička", "parent_id": parent.id}
        )
        self.assertEqual(child.l10n_sk_dic, "2020317068")

    def test_the_payroll_declarations_read_one_field(self):
        """l10n_sk_hr_payroll_monthly_tax_overview and _hlasenie used to declare
        res.company.l10n_sk_dic themselves, as a plain stored Char. Three
        definitions of one field is how a value ends up in a column the ORM has
        stopped reading. Assert the field is related, i.e. not stored."""
        field = self.env["res.company"]._fields["l10n_sk_dic"]
        self.assertTrue(field.related, "must be a view of the partner value")
        self.assertFalse(field.store, "a stored copy can diverge from the partner")

    def test_two_different_dic_values_in_one_write_are_refused(self):
        """Both company fields inverse onto the same partner value, so a call
        naming both with different numbers is last-write-wins by dict order.
        On a statutory identifier that must be an error, not a coin toss."""
        company = self.env["res.company"].create({"name": "Konflikt s.r.o."})
        with self.assertRaises(ValidationError):
            company.write(
                {"l10n_sk_dic": "2020317068", "income_tax_id": "1111111111"}
            )
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {"name": "Konflikt 2 s.r.o.",
                 "l10n_sk_dic": "2020317068", "income_tax_id": "1111111111"}
            )
        # The same number twice is not a conflict.
        company.write({"l10n_sk_dic": "2020317068", "income_tax_id": "2020317068"})
        self.assertEqual(company.partner_id.l10n_sk_dic, "2020317068")

