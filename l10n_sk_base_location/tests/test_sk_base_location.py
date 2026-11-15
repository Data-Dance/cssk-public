# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSkBaseLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sk = cls.env.ref("base.sk")
        cls.City = cls.env["res.city"]
        cls.Zip = cls.env["res.city.zip"]

    def _cities(self, name):
        return self.City.search([("country_id", "=", self.sk.id), ("name", "=", name)])

    def test_every_okres_and_every_city_has_a_postcode(self):
        states = self.env["res.country.state"].search([("country_id", "=", self.sk.id)])
        self.assertEqual(len(states), 79)
        cities = self.City.search([("country_id", "=", self.sk.id)])
        self.assertGreater(len(cities), 2900)
        no_zip = cities.filtered(lambda c: not c.zip_ids)
        self.assertFalse(no_zip, no_zip.mapped("name"))

    def test_homonymous_obce_stay_apart(self):
        """The data this replaces keyed an obec by its name, so namesakes
        merged into one city carrying all of their PSČ."""
        luckas = self._cities("Lúčka")
        self.assertEqual(len(luckas), 4)
        self.assertEqual(len(luckas.state_id), 4)
        for city in luckas:
            self.assertEqual(len(city.zip_ids), 1)

    def test_full_names_not_the_post_abbreviation(self):
        self.assertTrue(self._cities("Bohdanovce nad Trnavou"))
        self.assertFalse(self._cities("Bohdanovce n/Trnavou"))
        self.assertTrue(self.env.ref(
            "l10n_sk_base_location.sk_state_304").name.startswith(
                "okres Nové Mesto nad Váhom"))

    def test_picking_a_postcode_fills_the_address(self):
        psc = self.Zip.search([("name", "=", "974 01"),
                               ("city_id.name", "=", "Banská Bystrica")])
        self.assertEqual(len(psc), 1)
        partner = self.env["res.partner"].create({"name": "BB", "zip_id": psc.id})
        self.assertEqual(partner.zip, "974 01")
        self.assertEqual(partner.city, "Banská Bystrica")
        self.assertEqual(partner.country_id, self.sk)
        self.assertEqual(partner.state_id.code, "601")

    def test_bratislava_is_one_city_without_an_okres(self):
        bratislava = self._cities("Bratislava")
        self.assertEqual(len(bratislava), 1)
        self.assertFalse(bratislava.state_id)
        self.assertIn("851 01", bratislava.zip_ids.mapped("name"))
        self.assertFalse(self.City.search([("name", "=like", "Bratislava-%")]))

    def test_moving_a_partner_to_bratislava_clears_the_okres(self):
        """base_location's _check_zip demands the partner's state equal the
        city's; without clearing it, this write raised ValidationError."""
        bb = self.Zip.search([("name", "=", "974 01"),
                              ("city_id.name", "=", "Banská Bystrica")])
        ba = self.Zip.search([("name", "=", "851 01"),
                              ("city_id.name", "=", "Bratislava")])
        partner = self.env["res.partner"].create({"name": "Mover", "zip_id": bb.id})
        self.assertTrue(partner.state_id)
        partner.zip_id = ba
        self.assertFalse(partner.state_id)
        self.assertEqual(partner.city, "Bratislava")
