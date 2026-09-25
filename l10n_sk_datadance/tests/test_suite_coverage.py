# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the one-click SK bundle actually delivers.

The umbrella is how a customer gets this collection, so a module that is not
reachable from here — as a dependency, as a settings toggle, or as a bridge
that auto-installs behind two of them — effectively does not ship. Every module
built for SK was invisible this way until 2026-08-05, which is the failure this
asserts against.
"""

from odoo.modules.module import get_manifest
from odoo.tests import TransactionCase, tagged

# Every SK-facing module we expect a customer to be able to reach from the
# bundle, and how. Adding a module to the collection without adding it here is
# the mistake this catches.
EXPECTED_HARD_DEPENDENCIES = {
    "l10n_sk_inventarizacia",
}
# Bridges: glue that exists only where two optional pieces are both installed,
# and that installs itself when they are. Neither a dependency nor a toggle of
# the bundle, so the two sets above cannot describe them. Maps bridge -> the
# optional modules it exists for.
EXPECTED_AUTO_INSTALL = {
    "l10n_sk_dppo_fs": {"l10n_sk_dppo", "l10n_sk_fs"},
}
EXPECTED_TOGGLES = {
    "l10n_sk_account_move_template",
    "l10n_sk_zavierka",
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

    def test_bridges_auto_install_from_their_optional_pieces(self):
        """A bridge must reach the customer without anyone knowing it exists.

        ``l10n_sk_fs`` and ``l10n_sk_dppo`` left ``depends`` for toggles in
        19.0.1.2.0, and the DPPO↔závierka glue stayed behind in the umbrella —
        which made the bundle uninstallable on a clean database (the model it
        inherits was no longer in the graph). The glue now lives in a bridge;
        this asserts the bridge is wired the way that fix depends on.
        """
        for name, optional in EXPECTED_AUTO_INSTALL.items():
            manifest = self._manifest(name)
            self.assertIsNotNone(manifest, f"{name} is not on the addons path")
            self.assertTrue(manifest.get("auto_install"),
                            f"{name} is not auto_install, so nobody installs it")
            depends = set(manifest.get("depends", []))
            self.assertIn("l10n_sk_datadance", depends)
            self.assertLessEqual(
                optional, depends,
                f"{name} must depend on the optional modules it bridges")
            self.assertLessEqual(
                optional, self._toggle_fields(),
                f"{name} bridges modules the bundle offers no toggle for")

    def test_the_bundle_hard_depends_only_on_publishable_modules(self):
        """The licensing rule, restated for an AGPL bundle.

        Until 19.0.1.2.0 this umbrella was ``Other proprietary`` and the rule
        ran the other way: an AGPL dependency would have relicensed it, so
        every AGPL piece was reached through a toggle. The bundle is AGPL-3
        itself now and its dependencies are AGPL-3 with it. What must not
        happen is the reverse — a hard dependency on a module we may not
        publish (the OEEL-bound ``_ee`` bridges), which would make the
        published bundle uninstallable from the public repository. That is the
        same failure the toggles exist to prevent, so assert it directly.
        """
        offenders = {}
        for name in self.module.dependencies_id.mapped("name"):
            manifest = self._manifest(name)
            if manifest is None:
                continue  # not on this addons path at all
            licence = manifest.get("license") or ""
            if "AGPL" not in licence and not licence.startswith("LGPL"):
                offenders[name] = licence or "(no license)"
        self.assertFalse(
            offenders,
            "hard dependencies of the published bundle must be publishable: "
            f"{offenders}",
        )
