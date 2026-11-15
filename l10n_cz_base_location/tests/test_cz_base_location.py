# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzBaseLocation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cz = cls.env.ref("base.cz")
        cls.City = cls.env["res.city"]

    def _cities(self, name):
        return self.City.search([("country_id", "=", self.cz.id), ("name", "=", name)])

    def test_all_okresy_and_obce(self):
        """The data this replaces had 14 'okresy' (one per kraj) and lost
        912 obce to name collisions."""
        states = self.env["res.country.state"].search([("country_id", "=", self.cz.id)])
        self.assertEqual(len(states), 77)
        cities = self.City.search([("country_id", "=", self.cz.id)])
        self.assertGreater(len(cities), 6200)
        no_zip = cities.filtered(lambda c: not c.zip_ids)
        self.assertFalse(no_zip, no_zip.mapped("name"))

    def test_a_city_sits_in_its_own_okres(self):
        """Kladno was in 'okres Nymburk' before, like all of Středočeský kraj.
        (A second obec Kladno lies in okres Chrudim.)"""
        kladno = self._cities("Kladno").filtered(lambda c: c.zip_ids.filtered(
            lambda z: z.name == "27201"))
        self.assertEqual(len(kladno), 1)
        self.assertEqual(kladno.state_id.code, "3203")
        self.assertEqual(kladno.state_id.name, "okres Kladno, Středočeský kraj")

    def test_homonymous_obce_stay_apart(self):
        nova_ves = self._cities("Nová Ves")
        self.assertEqual(len(nova_ves), 14)
        self.assertGreater(len(nova_ves.state_id), 1)

    def test_praha_and_vysocina_names(self):
        praha = self._cities("Praha")
        self.assertEqual(praha.state_id.name, "Hlavní město Praha")
        jihlava = self._cities("Jihlava")
        self.assertEqual(jihlava.state_id.name, "okres Jihlava, Kraj Vysočina")

    def test_picking_a_postcode_fills_the_address(self):
        psc = self.env["res.city.zip"].search([("name", "=", "27201"),
                                               ("city_id.name", "=", "Kladno")])
        self.assertEqual(len(psc), 1)
        partner = self.env["res.partner"].create({"name": "Kladno", "zip_id": psc.id})
        self.assertEqual((partner.zip, partner.city), ("27201", "Kladno"))
        self.assertEqual(partner.country_id, self.cz)
        self.assertEqual(partner.state_id.code, "3203")

    def test_a_name_repeated_within_an_okres_gets_its_psc(self):
        """res.city is unique on (name, state, country); two okresy each hold
        two obce of one name, which failed the install outright."""
        brezina = self.City.search([("country_id", "=", self.cz.id),
                                    ("name", "=like", "Březina (%)")])
        self.assertEqual(sorted(brezina.mapped("name")),
                         ["Březina (66601)", "Březina (67905)"])
        self.assertEqual(len(brezina.state_id), 1)
