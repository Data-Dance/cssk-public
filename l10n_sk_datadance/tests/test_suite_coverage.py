# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""What the one-click SK bundle actually delivers.

The umbrella is how a customer gets this collection, so a module that is not
reachable from here — as a dependency or as a settings toggle — effectively does
not ship. Every module built for SK was invisible this way until 2026-08-08 on
this branch, which is the failure this asserts against.
"""

from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged

# Every SK-facing module we expect a customer to be able to reach from the
# bundle, and how. Adding a module to the collection without adding it here is
# the mistake this catches.
EXPECTED_HARD_DEPENDENCIES = {
    "l10n_sk_inventory_verification",
}
EXPECTED_TOGGLES = {
    "l10n_sk_account_move_template",
    "l10n_sk_fiscal_year_closing",
    "l10n_sk_account_loan_oca",
    "l10n_sk_asset_protocol_oca",
    "l10n_sk_jcd",
    "l10n_sk_vehicle_expense",
    "account_invoice_ai_extract",
    "l10n_sk_mis_reports",
    # pre-existing
    "currency_rate_update_sk",
    "l10n_sk_account_cutoff",
    "l10n_sk_payment_reliability",
    "l10n_sk_account_asset_tax",
    "l10n_sk_stock_account_method_a",
    "l10n_sk_sale_order_advance_invoice",
}


@tagged("post_install", "-at_install")
class TestSuiteCoverage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = cls.env.ref("base.module_l10n_sk_datadance")

    def _manifest(self, name):
        """Resolve a module anywhere on the addons path, not just next to us.

        Method A moved to its own repository (Data-Dance/stock_method_a) on
        2026-09-06, so a toggle can now name a module that is a sibling
        directory of nothing. What the bundle needs is that Odoo can find and
        install it, which is what the addons path answers.
        """
        return get_manifest(name) or None

    def _toggle_fields(self):
        return {
            fname[len("module_"):]
            for fname in self.env["res.config.settings"]._fields
            if fname.startswith("module_")
        }

    def test_expected_modules_are_reachable_from_the_bundle(self):
        depends = set(self.module.dependencies_id.mapped("name"))
        toggles = self._toggle_fields()

        missing = {
            name
            for name in EXPECTED_HARD_DEPENDENCIES
            if name not in depends
        }
        self.assertFalse(missing, f"not hard dependencies of the bundle: {missing}")

        missing = {name for name in EXPECTED_TOGGLES if name not in toggles}
        self.assertFalse(missing, f"no res.config.settings toggle: {missing}")

    def test_every_toggle_names_a_real_installable_module(self):
        """A typo in a module_* field name fails silently — the tick does nothing."""
        for name in EXPECTED_TOGGLES:
            manifest = self._manifest(name)
            self.assertIsNotNone(manifest, f"{name} is not on the addons path")
            self.assertTrue(
                manifest.get("installable", True), f"{name} is not installable"
            )

    def test_no_agpl_module_is_a_hard_dependency(self):
        """The licensing firewall this bundle is built on.

        AGPL is viral over network use, so hard-depending on an AGPL module
        would relicense the whole proprietary bundle. AGPL pieces are reached
        through settings toggles instead: ticking one installs it into the
        customer's database without this module depending on it. Asserted rather
        than trusted, because `depends` is the easiest place to get it wrong.
        """
        offenders = {}
        for name in self.module.dependencies_id.mapped("name"):
            manifest = self._manifest(name)
            if manifest and "AGPL" in (manifest.get("license") or ""):
                offenders[name] = manifest["license"]
        self.assertFalse(
            offenders,
            "AGPL modules must be toggles, not dependencies of a proprietary "
            f"bundle: {offenders}",
        )

    def test_hard_dependencies_are_all_proprietary(self):
        """The same rule stated positively, so a new licence type is noticed."""
        for name in self.module.dependencies_id.mapped("name"):
            manifest = self._manifest(name)
            if manifest is None:
                continue  # not on this addons path at all
            self.assertEqual(
                manifest.get("license"),
                "Other proprietary",
                f"{name} is a hard dependency but is not proprietary",
            )
