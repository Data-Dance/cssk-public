# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""How core 18.0's partner_autocomplete reaches ARES through the dispatcher.

Core's JS asks for suggestions with autocomplete_by_name / autocomplete_by_vat
and enriches every pick with enrich_by_duns. Those three are the only way in
on 18.0, so they are what is pinned here — with ARES itself mocked out.
"""
from unittest.mock import patch

from odoo.tests.common import TransactionCase

ARES = "partner.autocomplete.provider.ares_cz"


class TestAresDispatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_autocomplete_provider = ARES
        cls.Partner = cls.env["res.partner"]
        cls.provider_class = type(cls.env[ARES])

    def test_ares_is_a_selectable_provider(self):
        """If this fails, the company write in setUpClass set nothing useful
        and every other test here is exercising Odoo's IAP instead."""
        self.assertEqual(self.env.company.partner_autocomplete_provider, ARES)
        self.assertEqual(self.Partner._get_partner_autocomplete_provider()._name, ARES)

    def test_suggestions_come_from_ares(self):
        answer = [{"name": "Vzorová CZ s.r.o.", "partner_gid": "12345678", "duns": "12345678"}]
        with patch.object(self.provider_class, "autocomplete", return_value=answer):
            self.assertEqual(self.Partner.autocomplete_by_name("Vzorová", False), answer)

    def test_an_empty_vat_answer_is_not_a_blank_row(self):
        """ARES cannot search by DIČ and answers [{}]; core would render it."""
        with patch.object(self.provider_class, "read_by_vat", return_value=[{}]):
            self.assertEqual(self.Partner.autocomplete_by_vat("CZ12345678", False), [])

    def test_a_pick_is_enriched_by_ares_and_marked_as_such(self):
        answer = {"name": "Vzorová CZ s.r.o.", "vat": "CZ12345678"}
        with patch.object(self.provider_class, "enrich_company", return_value=answer) as enrich:
            data = self.Partner.enrich_by_duns("12345678")
        enrich.assert_called_once_with(None, "12345678", None)
        self.assertEqual(data["name"], "Vzorová CZ s.r.o.")
        # The JS suppresses core's Dun & Bradstreet chatter card on this key.
        self.assertEqual(data["partner_autocomplete_provider"], ARES)
        self.assertNotIn("error", data)

    def test_no_answer_is_reported_not_treated_as_success(self):
        """Core's JS treats {} as a successful enrichment: it writes nothing,
        says nothing, and posts an empty D&B card. An error makes it notify
        the user and fall back to the suggestion's own values."""
        with patch.object(self.provider_class, "enrich_company", return_value={}):
            data = self.Partner.enrich_by_duns("12345678")
        self.assertTrue(data["error"])
        self.assertIn("12345678", data["error_message"])

    def test_odoo_iap_stays_untouched(self):
        self.env.company.partner_autocomplete_provider = "partner.autocomplete.provider"
        self.assertIsNone(self.Partner._get_partner_autocomplete_provider())
        with patch.object(self.provider_class, "enrich_company") as enrich, patch(
            "odoo.addons.partner_autocomplete.models.res_partner.ResPartner.enrich_by_duns",
            return_value={"name": "From IAP"},
        ):
            self.assertEqual(self.Partner.enrich_by_duns("123"), {"name": "From IAP"})
        enrich.assert_not_called()
