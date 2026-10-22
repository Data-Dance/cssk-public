from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user

from odoo.addons.l10n_sk_vrp2_base.models.vrp2_client import (
    _compact_json,
    _crp_checksum,
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
