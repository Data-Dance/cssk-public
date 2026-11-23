# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The link between the employee records of one person that are taxed together."""

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxPrincipalLink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {"name": "SK taxed together", "country_id": cls.env.ref("base.sk").id}
        )
        cls.other_company = cls.env["res.company"].create(
            {"name": "SK other employer", "country_id": cls.env.ref("base.sk").id}
        )
        cls.env.user.company_ids |= cls.company | cls.other_company

    def _record(self, name, birth_number="850101/1234", company=None):
        return self.env["hr.employee"].create(
            {
                "name": name,
                "company_id": (company or self.company).id,
                "identification_id": birth_number,
            }
        )

    def test_one_record_taxes_the_month_for_the_others(self):
        employment = self._record("Employment")
        first = self._record("First agreement")
        second = self._record("Second agreement")
        (first | second).l10n_sk_tax_principal_id = employment
        self.assertEqual(employment.l10n_sk_tax_linked_ids, first | second)

    def test_no_chains(self):
        employment = self._record("Employment")
        agreement = self._record("Agreement")
        third = self._record("Third")
        agreement.l10n_sk_tax_principal_id = employment
        # Onto a record that is itself taxed on another.
        with self.assertRaises(ValidationError):
            third.l10n_sk_tax_principal_id = agreement
        # A record that taxes the month for another cannot be linked.
        with self.assertRaises(ValidationError):
            employment.l10n_sk_tax_principal_id = third
        with self.assertRaises(ValidationError):
            employment.l10n_sk_tax_principal_id = employment

    def test_same_company_only(self):
        employment = self._record("Employment")
        elsewhere = self._record("Elsewhere", company=self.other_company)
        with self.assertRaises(ValidationError):
            elsewhere.l10n_sk_tax_principal_id = employment
        agreement = self._record("Agreement")
        agreement.l10n_sk_tax_principal_id = employment
        with self.assertRaises(ValidationError):
            employment.company_id = self.other_company
        with self.assertRaises(ValidationError):
            agreement.company_id = self.other_company

    def test_one_person_by_the_birth_number(self):
        employment = self._record("Employment", birth_number="850101/1234")
        stranger = self._record("Stranger", birth_number="900202/4321")
        with self.assertRaises(ValidationError):
            stranger.l10n_sk_tax_principal_id = employment
        # The same number written without the slash is the same person.
        agreement = self._record("Agreement", birth_number="8501011234")
        agreement.l10n_sk_tax_principal_id = employment
        # A number changed afterwards is checked from either side.
        with self.assertRaises(ValidationError):
            agreement.identification_id = "900202/4321"
        with self.assertRaises(ValidationError):
            employment.identification_id = "900202/4321"

    def test_record_without_a_birth_number_is_the_officers_word(self):
        employment = self._record("Employment")
        agreement = self._record("Agreement", birth_number=False)
        agreement.l10n_sk_tax_principal_id = employment
        self.assertEqual(agreement.l10n_sk_tax_principal_id, employment)
