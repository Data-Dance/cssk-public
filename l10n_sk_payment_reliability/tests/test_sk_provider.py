# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

POST = "odoo.addons.l10n_sk_payment_reliability.models.res_partner.requests.get"


@tagged("post_install", "-at_install")
class TestSkProvider(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("fa_api_key", "TESTKEY")
        cls.partner = cls.env["res.partner"].create({
            "name": "Slovak Supplier s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "vat": "SK2023456787",
            "company_registry": "12345678",
        })

    def _resp(self, payload):
        m = MagicMock()
        m.raise_for_status.return_value = None
        m.json.return_value = payload
        return m

    def test_registered_accounts_parsed(self):
        with patch(POST, return_value=self._resp(
            {"data": [{"iban": "SK68 0720 0002 8919 8742 6353"}, {"iban": "SK1102000000001234567890"}]}
        )):
            accounts = self.partner._cssk_get_registered_accounts()
        self.assertEqual(
            accounts,
            ["SK6807200002891987426353", "SK1102000000001234567890"],
        )

    def test_reliability_index_mapped(self):
        with patch(POST, return_value=self._resp({"data": [{"ids": "menej spoľahlivý"}]})):
            self.assertEqual(self.partner._cssk_get_tax_reliability(), "less_reliable")
        with patch(POST, return_value=self._resp({"data": [{"ids": "vysoko spoľahlivý"}]})):
            self.assertEqual(self.partner._cssk_get_tax_reliability(), "highly_reliable")

    def test_no_api_key_returns_none(self):
        self.env["ir.config_parameter"].sudo().set_param("fa_api_key", "")
        self.assertIsNone(self.partner._cssk_get_registered_accounts())

    def test_network_error_returns_none(self):
        import requests as _r
        with patch(POST, side_effect=_r.exceptions.ConnectionError("boom")):
            self.assertIsNone(self.partner._cssk_get_registered_accounts())

    def test_non_sk_partner_falls_back(self):
        de = self.env["res.partner"].create({
            "name": "DE", "country_id": self.env.ref("base.de").id, "vat": "DE123"})
        # base hook returns None (no provider for non-SK)
        self.assertIsNone(de._cssk_get_registered_accounts())
