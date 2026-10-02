# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A Czech partner is looked up in ARES whatever the company's provider.

Two companies in two countries sharing contacts could each autocomplete only
from their own provider, so the Slovak one could not look up a Czech partner.
"""
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

ARES = "partner.autocomplete.provider.ares_cz"
NONE = "partner.autocomplete.provider"


@tagged("post_install", "-at_install")
class TestCountryDispatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.env.company.partner_autocomplete_provider = NONE

    def test_the_partner_country_picks_the_provider(self):
        self.assertEqual(self.Partner._autocomplete_provider_for("CZ"), ARES)
        self.assertEqual(self.Partner._autocomplete_provider_for("DE"), NONE)
        self.assertEqual(self.Partner._autocomplete_provider_for(None), NONE)

    def test_the_country_comes_from_the_query_then_the_vat_prefix(self):
        cz = self.env.ref("base.cz")
        self.assertEqual(self.Partner._autocomplete_country_code(cz.id), "CZ")
        self.assertEqual(
            self.Partner._autocomplete_country_code(None, "CZ25596641"), "CZ")
        self.assertEqual(
            self.Partner._autocomplete_country_code(None, "EL123456789"), "GR")
        self.assertIsNone(self.Partner._autocomplete_country_code(None, "25596641"))

    def test_a_czech_search_is_stamped_with_its_provider(self):
        with patch.object(
            type(self.env[ARES]), "autocomplete",
            return_value=[{"name": "Firma s.r.o.", "duns": "25596641"}],
        ) as called:
            result = self.Partner.autocomplete_by_name(
                "Firma", self.env.ref("base.cz").id)
        called.assert_called_once()
        self.assertEqual(result[0]["partner_autocomplete_provider"], ARES)

    def test_enrichment_goes_back_to_the_provider_of_the_suggestion(self):
        with patch.object(
            type(self.env[ARES]), "enrich_company",
            return_value={"name": "Firma s.r.o."},
        ) as called:
            self.Partner.with_context(enriched_company_data={
                "duns": "25596641", "partner_autocomplete_provider": ARES,
            }).enrich_by_duns("25596641")
        called.assert_called_once()

    def test_an_unknown_stamp_falls_back_to_the_company_provider(self):
        self.env.company.partner_autocomplete_provider = ARES
        with patch.object(
            type(self.env[ARES]), "enrich_company", return_value={},
        ) as called:
            self.Partner.with_context(enriched_company_data={
                "partner_autocomplete_provider": "no.such.model",
            }).enrich_by_duns("25596641")
        called.assert_called_once()
