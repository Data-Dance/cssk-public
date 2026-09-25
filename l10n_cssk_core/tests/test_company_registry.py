# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The IČO constraint on res.partner, and the two ways it must not overreach.

The check itself is pinned in ``test_tools``. What is pinned here is where it
applies: CZ/SK only, and only to a value the partner actually carries. Both
boundaries were found the expensive way. An unscoped check rejects Hetzner's
``HRB 6089`` and a US EIN, and a check that fires on an empty value makes every
private customer unsaveable at checkout.
"""
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCompanyRegistryConstraint(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk = cls.env.ref("base.sk")
        cls.cz = cls.env.ref("base.cz")
        cls.de = cls.env.ref("base.de")
        cls.us = cls.env.ref("base.us")

    def _partner(self, **vals):
        return self.env["res.partner"].create({"name": "Test", **vals})

    # -- accepts ------------------------------------------------------------

    def test_valid_sk_and_cz(self):
        self.assertTrue(self._partner(country_id=self.sk.id, company_registry="54093431"))
        self.assertTrue(self._partner(country_id=self.cz.id, company_registry="25380141"))

    def test_no_registry_is_fine(self):
        """A private customer has no IČO and must still be able to check out."""
        self.assertTrue(self._partner(country_id=self.sk.id))
        self.assertTrue(self._partner(country_id=self.sk.id, company_registry=False))

    def test_foreign_registry_is_not_checked(self):
        """The mod-11 scheme is Czechoslovak. Nowhere else uses it."""
        self.assertTrue(self._partner(country_id=self.de.id, company_registry="HRB 6089"))
        self.assertTrue(self._partner(country_id=self.us.id, company_registry="93-1564675"))

    def test_no_country_is_not_checked(self):
        """Signup captures an e-mail long before it captures a country."""
        self.assertTrue(self._partner(company_registry="whatever"))

    def test_a_foreign_vat_registration_does_not_pull_in_the_check(self):
        """A German company VAT-registered in Czechia carries a ``CZ…`` VAT
        number while its company registry is still its home register's.
        Deducing the country from the VAT prefix would reject ``HRB 6089``
        here, so the scope is keyed on the country instead."""
        partner = self._partner(
            country_id=self.de.id,
            vat="CZ25380141",
            company_registry="HRB 6089",
        )
        self.assertEqual(partner.company_registry, "HRB 6089")

    # -- rejects ------------------------------------------------------------

    def test_rejects_bad_checksum(self):
        with self.assertRaises(ValidationError):
            self._partner(country_id=self.sk.id, company_registry="20239413")

    def test_rejects_the_company_name(self):
        """The failure this exists for: three of these reached production, two
        of them onto posted invoices."""
        for value in ("TRAIVA, s.r.o.", "JUSTICE.CZ", "Test", "12345", "-"):
            with self.assertRaises(ValidationError, msg=f"{value!r} was accepted"):
                self._partner(country_id=self.cz.id, company_registry=value)

    def test_rejects_on_write_too(self):
        partner = self._partner(country_id=self.sk.id, company_registry="54093431")
        with self.assertRaises(ValidationError):
            partner.write({"company_registry": "12345"})

    def test_rejects_when_the_country_arrives_later(self):
        """Country and registry rarely arrive in the same write."""
        partner = self._partner(company_registry="12345")
        with self.assertRaises(ValidationError):
            partner.write({"country_id": self.sk.id})

    # -- canonicalisation ---------------------------------------------------

    def test_stores_the_padded_form(self):
        partner = self._partner(country_id=self.sk.id, company_registry="00 585 441")
        self.assertEqual(partner.company_registry, "00585441")

    def test_pads_an_unpadded_number(self):
        partner = self._partner(country_id=self.sk.id, company_registry="614556")
        self.assertEqual(partner.company_registry, "00614556")

    def test_canonicalisation_makes_cores_duplicate_check_work(self):
        """``same_company_registry_partner_id`` is an exact string match in
        core, so ``00 585 441`` and ``00585441`` would not see each other
        without this. Normalising at the storage layer is what makes core's
        own duplicate warning fire."""
        first = self._partner(country_id=self.sk.id, company_registry="00585441")
        second = self._partner(country_id=self.sk.id, company_registry="00 585 441")
        self.assertEqual(second.same_company_registry_partner_id, first)

    def test_foreign_registry_is_left_alone(self):
        partner = self._partner(country_id=self.de.id, company_registry="HRB 6089")
        self.assertEqual(partner.company_registry, "HRB 6089")

    def test_canonicalisation_does_not_loop(self):
        partner = self._partner(country_id=self.sk.id, company_registry="614556")
        partner.write({"company_registry": "00 585 441"})
        self.assertEqual(partner.company_registry, "00585441")

    def test_short_number_is_not_padded_into_validity(self):
        """``1`` zero-pads to ``00000001``, which satisfies the check digit.
        Neither the constraint nor the canonicaliser may let that through."""
        with self.assertRaises(ValidationError):
            self._partner(country_id=self.sk.id, company_registry="1")

    # -- reporting ----------------------------------------------------------

    def test_error_names_the_company_not_the_contact(self):
        """The registry is a commercial field, so a bad value on a parent
        reaches every child. The error must point at the company that owns
        the number, not at whichever contact was written first."""
        parent = self._partner(country_id=self.sk.id, is_company=True,
                               name="Bad Registry s.r.o.")
        child = self.env["res.partner"].create(
            {"name": "A Contact", "parent_id": parent.id}
        )
        with self.assertRaises(ValidationError) as caught:
            parent.write({"company_registry": "12345"})
        self.assertIn("Bad Registry s.r.o.", str(caught.exception))
        self.assertNotIn(child.name, str(caught.exception))
