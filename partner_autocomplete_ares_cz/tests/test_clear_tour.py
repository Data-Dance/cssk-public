# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import Command
from odoo.tests import HttpCase, tagged

ARES = "partner.autocomplete.provider.ares_cz"


@tagged("post_install", "-at_install")
class TestAresClearTour(HttpCase):
    def test_a_cleared_one2many_is_saved_cleared(self):
        """A register answer that replaces a one2many must replace it on save.

        The dispatcher's StaticList patch handles CLEAR on the client, but the
        list only sends the commands it has recorded, so wiping them left the
        old rows attached on the server: the form showed them gone until the
        next reload. partner_autocomplete_orsf_sk answers exactly this way for
        its activity, filing and history mirrors.
        """
        self.env.company.partner_autocomplete_provider = ARES
        company = self.env["res.partner"].create({
            "name": "Stale name s.r.o.",
            "is_company": True,
            "child_ids": [Command.create({"name": "Old Contact", "type": "contact"})],
        })
        old_contact = company.child_ids
        provider_class = type(self.env[ARES])
        suggestion = {"name": "Durwen CZ s.r.o.", "partner_gid": "12345678", "duns": "12345678"}
        enriched = {
            "name": "Durwen CZ s.r.o.",
            "vat": "CZ12345678",
            "partner_gid": "12345678",
            "child_ids": [
                Command.clear(),
                Command.create({"name": "New Contact", "type": "contact"}),
            ],
        }
        with patch.object(provider_class, "autocomplete", return_value=[suggestion]), \
                patch.object(provider_class, "enrich_company", return_value=enriched):
            self.start_tour(
                f"/odoo/action-base.action_partner_form/{company.id}",
                "partner_autocomplete_ares_clear",
                login="admin",
            )

        self.assertEqual(company.vat, "CZ12345678")
        self.assertEqual(company.child_ids.mapped("name"), ["New Contact"])
        self.assertNotEqual(old_contact.parent_id, company)
