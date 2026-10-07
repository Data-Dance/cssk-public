from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user

from odoo.addons.l10n_sk_vrp2_base.models.vrp2_client import (
    _compact_json,
    _crp_checksum,
    vrp2_round5,
)


@tagged("post_install", "-at_install")
class TestVrp2Base(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.vrp2_login = "88812345678900001"
        cls.company.vrp2_token = "SECRET-TOKEN"
        cls.user = new_test_user(
            cls.env, login="vrp2_plain_user", groups="base.group_user"
        )

    # ---- pure helpers ----------------------------------------------------

    def test_crp_checksum_stable(self):
        # Frozen vector (compact JSON + shifted token + SHA-256 + base64),
        # matching the deobfuscated VRP2 web-client algorithm.
        self.assertEqual(
            _crp_checksum(
                _compact_json(
                    {"priceWithVat": 12.3, "invoiceNumber": "FA-001"}
                ),
                "AbC123xyz",
            ),
            "cxfypeuih01qF21DJ7uJxcAQqvE6XyGA73KiYUl268Y=",
        )

    def test_round5_mirrors_the_web_app(self):
        """zaokruhli5 from app.js, including its two oddities: an amount
        under 5 cents rounds AWAY from zero, and a half rounds towards
        +infinity (JavaScript Math.round), so −1.025 → −1.00."""
        cases = {
            18.48: 18.5, 18.47: 18.45, 8.48: 8.5, 0: 0.0, 0.01: 0.05,
            -0.01: -0.05, 1.025: 1.05, -1.025: -1.0, -18.48: -18.5,
        }
        for amount, expected in cases.items():
            self.assertEqual(vrp2_round5(amount), expected, amount)

    def test_valid_receipt_header_comes_from_the_dashboard(self):
        dashboard = {"cashRegister": {
            "dkp": "99920201234560002", "version": 1662177617338,
            "organization": {"name": "X", "vatPayer": False},
        }}
        with patch.object(
            type(self.env["vrp2.client"]), "_get_dashboard",
            return_value=dashboard,
        ):
            header = self.company._vrp2_valid_receipt_header()
        self.assertEqual(
            header, {"vatPayer": False, "version": 1662177617338}
        )
        self.assertEqual(self.company.vrp2_register_version, "1662177617338")

    # ---- session-token protection (groups=base.group_system) --------------

    def test_token_not_readable_by_internal_users(self):
        """A live VRP2 session token must be admin-only."""
        with self.assertRaises(AccessError):
            self.company.with_user(self.user).vrp2_token  # noqa: B018

    def test_status_still_computes_for_internal_users(self):
        """The (non-sensitive) connection status stays visible to everyone
        even though it derives from the protected token."""
        self.assertEqual(
            self.company.with_user(self.user).vrp2_status, "connected"
        )

    def test_client_session_works_for_internal_users(self):
        """The client reads the token with elevated rights, so a normal user
        allowed to fiscalize can still open/reuse the session."""
        client = self.env["vrp2.client"].with_user(self.user)
        with patch.object(
            type(self.env["vrp2.client"]), "_request_raw",
            side_effect=AssertionError("token present — no network expected"),
        ):
            token = client._ensure_session(self.company.with_user(self.user))
        self.assertEqual(token, "SECRET-TOKEN")
