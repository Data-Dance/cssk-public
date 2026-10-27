# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Searching ARES by IČO and by DIČ, and *Update* routed by country.

No network: ``enrich_company`` (the one ARES request) is patched, so these pin
what the module does with an answer, not what ARES answers.
"""
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

ARES = "partner.autocomplete.provider.ares_cz"
IAP = "partner.autocomplete.provider"
NONE = "partner.autocomplete.provider.none"

FIRMA = {
    "name": "Firma s.r.o.",
    "street": "Na Příkopě 1",
    "city": "Praha",
    "zip": "11000",
    "vat": "CZ25596641",
    "partner_gid": "25596641",
    "partner_autocomplete_provider": ARES,
}


@tagged("post_install", "-at_install")
class TestAresSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ares = cls.env[ARES]
        # The IČO mapping is deliberately NOT pointed at company_registry:
        # the search used to work only when it was.
        cls.env["ir.config_parameter"].sudo().set_param("ares_cz.mapping.ico", False)

    def _enrich(self, data):
        return patch.object(type(self.Ares), "enrich_company", return_value=data)

    def test_an_ico_search_offers_a_suggestion_that_can_be_enriched(self):
        with self._enrich(dict(FIRMA)) as called:
            result = self.Ares.autocomplete("25596641")
        called.assert_called_once_with(None, "25596641", None)
        self.assertEqual(len(result), 1)
        # What the widget sends back to enrich_by_duns.
        self.assertEqual(result[0]["duns"], "25596641")
        self.assertEqual(result[0]["partner_gid"], "25596641")
        self.assertEqual(result[0]["website"], "25596641 | Praha")

    def test_a_subject_without_a_city_still_gives_a_suggestion(self):
        data = dict(FIRMA)
        del data["city"]
        with self._enrich(data):
            result = self.Ares.autocomplete("25596641")
        self.assertEqual(result[0]["website"], "25596641 | ")

    def test_an_unknown_ico_offers_nothing(self):
        with self._enrich({}):
            self.assertEqual(self.Ares.autocomplete("99999999"), [])

    def test_a_czech_dic_finds_its_company(self):
        with self._enrich(dict(FIRMA)) as called:
            result = self.Ares.read_by_vat("CZ25596641")
        called.assert_called_once_with(None, "25596641", None)
        self.assertEqual([r["name"] for r in result], ["Firma s.r.o."])
        self.assertEqual(result[0]["duns"], "25596641")

    def test_a_dic_ares_does_not_confirm_finds_nothing(self):
        # The IČO exists, but ARES gives it another (or no) DIČ.
        with self._enrich(dict(FIRMA, vat="")):
            self.assertEqual(self.Ares.read_by_vat("CZ25596641"), [])
        # A natural person's DIČ is a birth number: no IČO to try.
        with self._enrich(dict(FIRMA)) as called:
            self.assertEqual(self.Ares.read_by_vat("CZ8001011234"), [])
        called.assert_not_called()


@tagged("post_install", "-at_install")
class TestUpdateRouting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_autocomplete_provider = IAP
        cls.partner = cls.env["res.partner"].create({
            "name": "Ručně zadaná firma",
            "is_company": True,
            "company_registry": "25596641",
            "country_id": cls.env.ref("base.cz").id,
        })

    def test_update_asks_the_register_of_the_partner_s_country(self):
        """A Czech contact typed in by hand, in a company whose own provider is
        another one, used to be looked up by that other provider."""
        with patch.object(
            type(self.env[ARES]), "enrich_company", return_value=dict(FIRMA),
        ) as called:
            self.partner._update_partner_info()
        called.assert_called_once()
        self.assertEqual(self.partner.name, "Firma s.r.o.")

    def test_update_prefers_the_provider_recorded_on_the_partner(self):
        self.partner.country_id = self.env.ref("base.de")
        self.partner.partner_autocomplete_provider = ARES
        with patch.object(
            type(self.env[ARES]), "enrich_company", return_value=dict(FIRMA),
        ) as called:
            self.partner._update_partner_info()
        called.assert_called_once()


@tagged("post_install", "-at_install")
class TestNoneProvider(TransactionCase):
    def test_none_sends_nothing_to_odoo_iap(self):
        """"None" used to be the IAP fall-through under another name."""
        self.env.company.partner_autocomplete_provider = NONE
        Partner = self.env["res.partner"]
        with patch.object(
            type(self.env["iap.autocomplete.api"]), "_request_partner_autocomplete",
            side_effect=AssertionError("IAP must not be asked"),
        ):
            self.assertEqual(
                Partner.autocomplete_by_name("Siemens", self.env.ref("base.de").id), [])
            self.assertEqual(
                Partner.autocomplete_by_vat("DE129273398", self.env.ref("base.de").id), [])

    def test_none_still_reads_the_national_register(self):
        self.env.company.partner_autocomplete_provider = NONE
        with patch.object(
            type(self.env[ARES]), "autocomplete", return_value=[{"name": "Firma"}],
        ) as called:
            self.env["res.partner"].autocomplete_by_name(
                "Firma", self.env.ref("base.cz").id)
        called.assert_called_once()

    def test_the_iap_choice_is_labelled_as_such(self):
        labels = dict(
            self.env["partner.autocomplete.provider.registry"]._get_available_providers())
        self.assertEqual(labels[IAP], "Odoo IAP")
        self.assertEqual(labels[NONE], "None")
