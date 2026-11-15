# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The veřejný rejstřík entry: coordinates, status, dates and lists.

No network. Both ARES requests are patched with synthetic answers shaped like
the real ones (``ekonomicke-subjekty/{ico}`` and
``ekonomicke-subjekty-vr/{ico}``); the subject does not exist.
"""
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

ARES = "partner.autocomplete.provider.ares_cz"
MODULE = "odoo.addons.partner_autocomplete_ares_cz.models.partner_autocomplete_provider"
# Synthetic: passes the mod-11 check, and ARES held no such subject when the
# fixture was written.
ICO = "87654326"

BASIC = {
    "ico": ICO,
    "obchodniJmeno": "Zkušební výrobní s.r.o.",
    "sidlo": {
        "kodStatu": "CZ",
        "nazevObce": "Vzorov",
        "psc": 10000,
        "textovaAdresa": "Vzorová 1/2, 10000 Vzorov",
    },
    "dic": "CZ" + ICO,
    "datumVzniku": "2004-03-01",
    "seznamRegistraci": {
        "stavZdrojeVr": "AKTIVNI",
        "stavZdrojeRzp": "AKTIVNI",
        "stavZdrojeRos": "AKTIVNI",
    },
}
ENTRY = {
    "icoId": ICO,
    "zaznamy": [{
        "rejstrik": "OR",
        "primarniZaznam": True,
        "stavSubjektu": "AKTIVNI",
        "spisovaZnacka": [
            {"datumZapisu": "2004-03-01", "datumVymazu": "2010-06-01",
             "soud": "KSBR", "oddil": "C", "vlozka": 111},
            {"datumZapisu": "2010-06-01", "soud": "MSPH", "oddil": "C",
             "vlozka": 12345},
        ],
        "obchodniJmeno": [
            {"datumZapisu": "2004-03-01", "datumVymazu": "2010-06-01",
             "hodnota": "Stará zkušební s.r.o."},
            {"datumZapisu": "2010-06-01", "hodnota": "Zkušební výrobní s.r.o."},
        ],
        "adresy": [
            {"datumZapisu": "2004-03-01", "datumVymazu": "2010-06-01",
             "typAdresy": "SIDLO",
             "adresa": {"textovaAdresa": "Původní 9, 60200 Vzorov"}},
            {"datumZapisu": "2010-06-01", "typAdresy": "SIDLO",
             "adresa": {"textovaAdresa": "Vzorová 1/2, 10000 Vzorov"}},
        ],
        "cinnosti": {
            "predmetPodnikani": [
                {"datumZapisu": "2004-03-01", "datumVymazu": "2012-01-01",
                 "hodnota": "Koupě zboží za účelem jeho dalšího\nprodeje"},
                {"datumZapisu": "2012-01-01",
                 "hodnota": "Výroba, obchod a služby neuvedené v přílohách 1 "
                            "až 3 živnostenského zákona"},
            ],
            "predmetCinnosti": [
                {"datumZapisu": "2015-05-05", "hodnota": "Správa vlastního majetku"},
            ],
        },
    }],
}


def _response(status, body=None):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = body
    return response


@tagged("post_install", "-at_install")
class TestAresRegister(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ares = cls.env[ARES]
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        # One request less to fake: the prevailing NACE is not this test's.
        cls.ICP.set_param("ares_cz.mapping.nace", False)
        cls.has_twin = "l10n_cz_register_name" in cls.env["res.partner"]._fields

    def _map(self, suffix, field_name):
        field = self.env["ir.model.fields"].sudo().search(
            [("model", "=", "res.partner"), ("name", "=", field_name)], limit=1)
        self.ICP.set_param(f"ares_cz.mapping.{suffix}", str(field.id))

    def _unmap_register(self):
        for parameter in self.Ares.DEFAULT_MAPPINGS:
            self.ICP.set_param(parameter, False)

    def _enrich(self, basic=None, entry=ENTRY, entry_status=200):
        """Run ``enrich_company`` against the two faked ARES answers."""
        self.asked = []

        def get(url, **_kwargs):
            self.asked.append(url)
            return _response(entry_status, entry)

        session = MagicMock()
        session.get.return_value = _response(200, basic or BASIC)
        with patch(f"{MODULE}.requests.Session", return_value=session), patch(
                f"{MODULE}.requests.get", side_effect=get):
            return self.Ares.enrich_company(None, ICO, None)

    def test_the_fixture_ico_passes_the_check_digit(self):
        digits = [int(d) for d in ICO]
        total = sum(d * w for d, w in zip(digits[:7], range(8, 1, -1)))
        self.assertEqual((11 - total % 11) % 10, digits[7])

    def test_coordinates_follow_a_mapping_to_any_text_field(self):
        """The mapping is the mechanism: it works with no sibling module."""
        self._unmap_register()
        self._map("register", "function")
        self._map("register_office", "ref")
        self._map("register_number", "comment")
        result = self._enrich()
        self.assertEqual(result["function"], "Obchodní rejstřík")
        # The entry in force, not the deleted one of the earlier court.
        self.assertEqual(result["ref"], "Městský soud v Praze")
        self.assertEqual(result["comment"], "C 12345")
        self.assertEqual(len(self.asked), 1)
        self.assertTrue(self.asked[0].endswith(f"/ekonomicke-subjekty-vr/{ICO}"))

    def test_the_register_is_not_asked_when_nothing_would_receive_it(self):
        if self.has_twin:
            self.skipTest("l10n_cz_trade_registry is installed: it always asks")
        self._unmap_register()
        result = self._enrich()
        self.assertEqual(self.asked, [])
        self.assertEqual(result["name"], "Zkušební výrobní s.r.o.")

    def test_dates_and_status_come_from_the_basic_record(self):
        self._unmap_register()
        self._map("status", "function")
        # Base gives a contact no date field of its own to aim at.
        date_field = self.env["ir.model.fields"].sudo().search(
            [("model", "=", "res.partner"), ("ttype", "=", "date"),
             ("store", "=", True), ("readonly", "=", False)], limit=1)
        if date_field:
            self._map("dissolved_date", date_field.name)
        result = self._enrich(basic=dict(BASIC, datumZaniku="2020-02-02"))
        if date_field:
            self.assertEqual(str(result[date_field.name]), "2020-02-02")
        if self.has_twin:
            self.assertEqual(result["function"], "active")
        else:
            self.assertEqual(result["function"], "AKTIVNI")

    def test_a_sole_trader_in_no_public_register_states_the_other_evidence(self):
        self._unmap_register()
        self._map("register", "function")
        self._map("register_office", "ref")
        basic = dict(BASIC, seznamRegistraci={
            "stavZdrojeVr": "NEEXISTUJICI", "stavZdrojeRzp": "AKTIVNI"})
        result = self._enrich(basic=basic, entry=None, entry_status=404)
        self.assertEqual(result["function"], "Živnostenský rejstřík")
        self.assertNotIn("ref", result)

    def test_an_unknown_court_code_writes_nothing(self):
        self._unmap_register()
        self._map("register_office", "ref")
        entry = {"zaznamy": [dict(ENTRY["zaznamy"][0], spisovaZnacka=[
            {"datumZapisu": "2010-06-01", "soud": "XXXX", "oddil": "C", "vlozka": 5}])]}
        self.assertNotIn("ref", self._enrich(entry=entry))

    def test_the_sibling_module_is_filled_by_default(self):
        if not self.has_twin:
            self.skipTest("l10n_cz_trade_registry is not installed")
        self._unmap_register()
        self.Ares._ares_apply_default_mappings()
        result = self._enrich(basic=dict(BASIC, datumZaniku="2020-02-02"))
        self.assertEqual(result["l10n_cz_register_name"], "Obchodní rejstřík")
        self.assertEqual(result["l10n_cz_register_office"], "Městský soud v Praze")
        self.assertEqual(result["l10n_cz_register_number"], "C 12345")
        self.assertEqual(result["l10n_cz_register_status"], "active")
        self.assertEqual(str(result["l10n_cz_established_on"]), "2004-03-01")
        self.assertEqual(str(result["l10n_cz_dissolved_on"]), "2020-02-02")
        self.assertTrue(result["l10n_cz_register_checked_on"])

        partner = self.env["res.partner"].create({"name": "X", "is_company": True})
        partner.write({k: v for k, v in result.items() if k.startswith("l10n_cz_")})
        self.assertEqual(
            partner.l10n_cz_trade_registry_statement,
            "Obchodní rejstřík vedený Městským soudem v Praze, "
            "oddíl C, vložka 12345",
        )
        activities = partner.l10n_cz_activity_ids
        self.assertEqual(len(activities), 3)
        self.assertEqual(
            sorted(activities.mapped("kind")), ["activity", "business", "business"])
        # The register's fixed-width line break is folded away.
        self.assertIn(
            "Koupě zboží za účelem jeho dalšího prodeje", activities.mapped("name"))
        self.assertEqual(len(activities.filtered("is_current")), 2)
        history = partner.l10n_cz_history_ids
        self.assertEqual(
            sorted(history.mapped("value")),
            ["Původní 9, 60200 Vzorov", "Stará zkušební s.r.o."])
        # Enriching again replaces the lists instead of doubling them.
        partner.write({k: v for k, v in result.items() if k.endswith("_ids")})
        self.assertEqual(len(partner.l10n_cz_activity_ids), 3)

    def test_an_unanswered_register_leaves_the_lists_alone(self):
        """"ARES did not answer" must not read as "nothing is entered"."""
        if not self.has_twin:
            self.skipTest("l10n_cz_trade_registry is not installed")
        result = self._enrich(entry=None, entry_status=503)
        self.assertNotIn("l10n_cz_activity_ids", result)
        self.assertNotIn("l10n_cz_history_ids", result)
        self.assertEqual(result["name"], "Zkušební výrobní s.r.o.")
