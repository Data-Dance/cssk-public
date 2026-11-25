# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the one-click CZ bundle reaches, as the Slovak suite asserts it.

A module that is neither a dependency nor a switch of the bundle has to be
found in the Apps list by name, which is how five Czech modules sat unused.
"""

from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged

EXPECTED_TOGGLES = {
    "currency_rate_update_cz",
    "l10n_cz_account_cutoff",
    "l10n_cz_payment_reliability",
    "l10n_cz_account_asset_tax",
    "l10n_cz_stock_account_method_a",
    "l10n_cz_sale_order_advance_invoice",
    "l10n_cz_account_move_template",
    "l10n_cz_fiscal_year_closing",
    "l10n_cz_asset_protocol_oca",
    "l10n_cz_mis_reports",
    "account_invoice_ai_extract",
    "l10n_cz_fs",
    "l10n_cz_dppo",
}
#: Switches whose module is delivered outside this repository: inert where
#: the module is not on the addons path, so their absence is not an error.
DELIVERED_SEPARATELY = {
    "l10n_cz_stock_account_method_a",
    "account_invoice_ai_extract",
    "l10n_cz_fs",
    "l10n_cz_dppo",
}


@tagged("post_install", "-at_install")
class TestCzSuiteCoverage(TransactionCase):

    def test_every_expected_module_has_a_switch(self):
        fields = self.env["res.config.settings"]._fields
        missing = {name for name in EXPECTED_TOGGLES
                   if "module_%s" % name not in fields}
        self.assertFalse(missing, "no res.config.settings switch: %s" % missing)

    def test_every_switch_is_in_the_settings_view(self):
        """A field with no place in the view cannot be ticked."""
        arch = self.env["res.config.settings"].get_view(view_type="form")[
            "arch"]
        missing = {name for name in EXPECTED_TOGGLES
                   if 'name="module_%s"' % name not in arch}
        self.assertFalse(missing, "not in the settings form: %s" % missing)

    def test_every_switch_names_a_real_installable_module(self):
        """A typo in a module_* field name fails silently: the tick does
        nothing."""
        for name in sorted(EXPECTED_TOGGLES):
            manifest = get_manifest(name)
            if not manifest and name in DELIVERED_SEPARATELY:
                continue
            self.assertTrue(manifest, "%s is not on the addons path" % name)
            self.assertTrue(manifest.get("installable", True),
                            "%s is not installable" % name)
