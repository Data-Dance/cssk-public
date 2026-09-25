# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for the related-party graph parser.

The payloads below are **synthetic**: ORSF's OpenAPI spec documents no schema
for the graph body, and the endpoint is gated, so there is no live sample to
copy. They are written in the two graphology dialects the parser claims to
accept, and that claim is what these tests pin. They do not prove the parser
matches ORSF's real output — only that it behaves as documented for the shapes
it says it handles.
"""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

PROVIDER = (
    "odoo.addons.partner_autocomplete_orsf_sk.models.partner_autocomplete_provider"
    ".PartnerAutocompleteProviderOrsfSk"
)
GET = f"{PROVIDER}._orsf_get"
COOKIES = f"{PROVIDER}._orsf_cookies"

# graphology's canonical serialisation: key + nested attributes.
NESTED_GRAPH = {
    "nodes": [
        {"key": "c:31333532", "attributes": {"kind": "company", "label": "ESET, spol. s r.o.", "ico": "31333532"}},
        {"key": "p:1", "attributes": {"kind": "person", "label": "Jana Nováková"}},
        {"key": "c:44444444", "attributes": {"kind": "company", "label": "Druhá s.r.o.", "ico": "44444444"}},
        {"key": "c:55555555", "attributes": {"kind": "company", "label": "Nesúvisiaca s.r.o.", "ico": "55555555"}},
    ],
    "edges": [
        {"source": "c:31333532", "target": "p:1", "attributes": {"role": "konateľ"}},
        {"source": "p:1", "target": "c:44444444", "attributes": {"role": "spoločník"}},
        # No path from the origin to this one.
        {"source": "c:55555555", "target": "p:99", "attributes": {"role": "konateľ"}},
    ],
}

# The flattened dialect several exporters emit.
FLAT_GRAPH = {
    "nodes": [
        {"id": "c:31333532", "type": "company", "name": "ESET, spol. s r.o.", "nationalId": "31333532"},
        {"id": "p:1", "type": "person", "name": "Jana Nováková"},
        {"id": "c:44444444", "type": "company", "name": "Druhá s.r.o.", "nationalId": "44444444"},
    ],
    "edges": [
        {"source": "c:31333532", "target": "p:1", "role": "konateľ"},
        {"source": "p:1", "target": "c:44444444", "role": "spoločník"},
    ],
}


@tagged("post_install", "-at_install")
class TestRelatedPartyParsing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "ESET, spol. s r.o.", "is_company": True,
             "company_registry": "31333532"}
        )

    def _rows(self, graph):
        return self.env["res.partner"]._orsf_sk_parse_graph(graph, "31333532")

    def test_nested_dialect(self):
        rows = self._rows(NESTED_GRAPH)
        by_name = {r["related_name"]: r for r in rows}
        self.assertEqual(set(by_name), {"Jana Nováková", "Druhá s.r.o."})
        self.assertEqual(by_name["Jana Nováková"]["degree"], 1)
        self.assertEqual(by_name["Jana Nováková"]["link_role"], "konateľ")
        self.assertEqual(by_name["Druhá s.r.o."]["degree"], 2)
        self.assertEqual(by_name["Druhá s.r.o."]["related_ico"], "44444444")
        self.assertEqual(by_name["Druhá s.r.o."]["link_person"], "Jana Nováková")

    def test_flattened_dialect_gives_the_same_answer(self):
        nested = {r["related_name"]: r["degree"] for r in self._rows(NESTED_GRAPH)}
        flat = {r["related_name"]: r["degree"] for r in self._rows(FLAT_GRAPH)}
        self.assertEqual(flat, nested)

    def test_an_unconnected_company_is_not_a_related_party(self):
        names = {r["related_name"] for r in self._rows(NESTED_GRAPH)}
        self.assertNotIn("Nesúvisiaca s.r.o.", names)

    def test_the_origin_is_never_its_own_related_party(self):
        names = {r["related_name"] for r in self._rows(NESTED_GRAPH)}
        self.assertNotIn("ESET, spol. s r.o.", names)

    def test_an_unrecognised_shape_yields_nothing_rather_than_guesses(self):
        for graph in ({}, {"nodes": "x", "edges": []}, {"elements": []},
                      {"nodes": [None, 1], "edges": [None]}):
            self.assertEqual(self._rows(graph), [], graph)

    # -- the action --------------------------------------------------------

    def test_fetching_requires_an_ico(self):
        bare = self.env["res.partner"].create({"name": "Bez IČO"})
        with self.assertRaisesRegex(UserError, "IČO"):
            bare.action_orsf_sk_fetch_related_parties()

    def test_fetching_says_plainly_that_it_needs_credentials(self):
        with patch(COOKIES, return_value=None):
            with self.assertRaisesRegex(UserError, "e-mail and password"):
                self.partner.action_orsf_sk_fetch_related_parties()

    def test_fetching_is_one_partner_at_a_time(self):
        """ensure_one is what keeps this off a list selection — ORSF asks."""
        other = self.env["res.partner"].create(
            {"name": "Iná", "company_registry": "44444444"}
        )
        with self.assertRaises(ValueError):
            (self.partner | other).action_orsf_sk_fetch_related_parties()

    def test_a_successful_fetch_records_and_links(self):
        neighbour = self.env["res.partner"].create(
            {"name": "Druhá s.r.o.", "is_company": True,
             "company_registry": "44444444"}
        )
        with patch(COOKIES, return_value={"__Secure-orsf.session_token": "x"}), \
                patch(GET, return_value=NESTED_GRAPH):
            self.partner.action_orsf_sk_fetch_related_parties()

        rows = self.partner.orsf_sk_related_party_ids
        self.assertEqual(len(rows), 2)
        self.assertTrue(self.partner.orsf_sk_related_parties_fetched_at)
        linked = rows.filtered(lambda r: r.related_ico == "44444444")
        self.assertEqual(linked.related_partner_id, neighbour)
        # The person has no IČO, so there is nothing to link them to.
        person = rows.filtered(lambda r: r.degree == 1)
        self.assertFalse(person.related_partner_id)

    def test_refetching_replaces_rather_than_accumulates(self):
        with patch(COOKIES, return_value={"__Secure-orsf.session_token": "x"}), \
                patch(GET, return_value=NESTED_GRAPH):
            self.partner.action_orsf_sk_fetch_related_parties()
            self.partner.action_orsf_sk_fetch_related_parties()
        self.assertEqual(len(self.partner.orsf_sk_related_party_ids), 2)

    def test_an_outage_is_reported_not_swallowed(self):
        with patch(COOKIES, return_value={"__Secure-orsf.session_token": "x"}), \
                patch(GET, return_value=None):
            with self.assertRaisesRegex(UserError, "no graph"):
                self.partner.action_orsf_sk_fetch_related_parties()
