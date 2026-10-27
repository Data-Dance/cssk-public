# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import importlib.util
import os

from odoo.tests import TransactionCase, tagged

NONE = "partner.autocomplete.provider.none"
IAP = "partner.autocomplete.provider"


@tagged("post_install", "-at_install")
class TestProviderDefault(TransactionCase):
    def test_a_new_company_sends_nothing_to_odoo(self):
        company = self.env["res.company"].create({"name": "Default provider Co"})
        self.assertEqual(company.partner_autocomplete_provider, NONE)

    def test_upgrade_moves_the_old_none_to_the_real_none(self):
        """Until 19.0.1.2.0 "None" was the label of Odoo IAP (and the
        default); the 19.0.1.3.0 migration moves such companies to None and
        leaves any other choice alone."""
        old_none = self.env["res.company"].create({"name": "Old none Co"})
        old_none.partner_autocomplete_provider = IAP
        other = self.env["res.company"].create({"name": "Kept Co"})
        other.partner_autocomplete_provider = NONE
        self.env.flush_all()
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "migrations", "19.0.1.3.0", "post-migrate.py")
        spec = importlib.util.spec_from_file_location("pad_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.migrate(self.env.cr, "19.0.1.2.0")
        self.env.invalidate_all()
        self.assertEqual(old_none.partner_autocomplete_provider, NONE)
        self.assertEqual(other.partner_autocomplete_provider, NONE)
