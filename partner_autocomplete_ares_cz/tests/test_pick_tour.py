# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
from unittest.mock import patch

from odoo.tests import HttpCase, tagged

ARES = "partner.autocomplete.provider.ares_cz"


@tagged("post_install", "-at_install")
class TestAresPickTour(HttpCase):
    def test_pick_an_ares_suggestion(self):
        """End to end through core 18.0's JS: suggestion, enrichment, update.

        Asserts what the browser cannot see — that the partner was saved with
        the register's data, and that core's Dun & Bradstreet chatter card was
        not posted for it.
        """
        self.env.company.partner_autocomplete_provider = ARES
        cz = self.env.ref("base.cz")
        provider_class = type(self.env[ARES])
        suggestion = {
            "name": "Vzorová CZ s.r.o.",
            "partner_gid": "12345678",
            "duns": "12345678",
            "vat": "CZ12345678",
            "country_id": False,
        }
        enriched = {
            "name": "Vzorová CZ s.r.o.",
            "street": "Na Příkopě 1",
            "city": "Praha",
            "zip": "11000",
            "vat": "CZ12345678",
            "country_id": {"id": cz.id, "display_name": cz.display_name},
            "partner_gid": "12345678",
        }
        with patch.object(provider_class, "autocomplete", return_value=[suggestion]), \
                patch.object(provider_class, "enrich_company", return_value=enriched):
            self.start_tour("/odoo", "partner_autocomplete_ares_pick", login="admin")

        partner = self.env["res.partner"].search([("vat", "=", "CZ12345678")])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.city, "Praha")
        self.assertEqual(partner.country_id, cz)
        self.assertEqual(partner.partner_gid, "12345678")
        self.assertEqual(partner.partner_autocomplete_provider, ARES)
        self.assertFalse(
            partner.message_ids.filtered(
                lambda m: "o_partner_autocomplete_enrich_info" in (m.body or "")
            ),
            "core's D&B card has no business on a register answer",
        )
