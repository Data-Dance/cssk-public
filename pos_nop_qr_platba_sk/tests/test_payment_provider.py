from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentProvider(TransactionCase):

    def test_qr_platba_provider_exists(self):
        provider = self.env["payment.provider"].search([("code", "=", "qr_platba_sk")], limit=1)
        self.assertTrue(provider, "The QR Platba payment provider must be created by data XML.")
        self.assertEqual(provider.code, "qr_platba_sk")

    def test_qr_platba_payment_method_exists(self):
        method = self.env["payment.method"].search([("code", "=", "qr_platba_sk")], limit=1)
        self.assertTrue(method)
        self.assertFalse(method.support_tokenization)

    def test_qr_platba_supports_only_eur(self):
        provider = self.env["payment.provider"].search([("code", "=", "qr_platba_sk")], limit=1)
        supported = provider._get_supported_currencies()
        self.assertTrue(all(c.name == "EUR" for c in supported))

    def test_qr_platba_default_payment_method_codes(self):
        provider = self.env["payment.provider"].search([("code", "=", "qr_platba_sk")], limit=1)
        self.assertIn("qr_platba_sk", provider._get_default_payment_method_codes())
