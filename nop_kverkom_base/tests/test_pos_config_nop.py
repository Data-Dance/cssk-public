import base64

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NopBaseCase, TEST_POKLADNICA, TEST_VATSK, _make_self_signed_cert


@tagged("post_install", "-at_install")
class TestPosConfigNop(NopBaseCase):

    def test_identity_parsed_from_cert(self):
        self.assertEqual(self.nop_pos_config.nop_vatsk, TEST_VATSK)
        self.assertEqual(self.nop_pos_config.nop_pokladnica_id_ext, TEST_POKLADNICA)

    def test_endpoints_follow_environment(self):
        self.nop_pos_config.nop_environment = "int"
        self.assertEqual(self.nop_pos_config.nop_erp_api_url, "https://api-erp-i.kverkom.sk")
        self.nop_pos_config.nop_environment = "prod"
        self.assertEqual(self.nop_pos_config.nop_erp_api_url, "https://api-erp.kverkom.sk")

    def test_invalid_cert_rejected(self):
        with self.assertRaises(ValidationError):
            self.nop_pos_config.write({
                "nop_int_client_cert_pem": base64.b64encode(b"not a certificate"),
            })

    def test_subject_without_vatsk_rejected(self):
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        from datetime import datetime, timedelta

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "not-a-pokladnica")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(1)
            .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
            .not_valid_after(datetime.utcnow() + timedelta(days=1))
            .sign(key, hashes.SHA256(), default_backend())
        )
        pem = cert.public_bytes(serialization.Encoding.PEM)
        with self.assertRaises(ValidationError):
            self.nop_pos_config.write({"nop_int_client_cert_pem": base64.b64encode(pem)})

    def test_both_env_certs_can_coexist(self):
        cert_pem, key_pem = _make_self_signed_cert()
        self.nop_pos_config.write({
            "nop_prod_client_cert_pem": base64.b64encode(cert_pem),
            "nop_prod_client_key_pem": base64.b64encode(key_pem),
        })
        self.assertTrue(self.nop_pos_config.nop_has_int_cert)
        self.assertTrue(self.nop_pos_config.nop_has_prod_cert)

        self.nop_pos_config.nop_environment = "int"
        int_cert, int_key, _ca = self.nop_pos_config._get_active_nop_cert_material()
        self.assertEqual(int_cert, self.nop_pos_config.nop_int_client_cert_pem)

        self.nop_pos_config.nop_environment = "prod"
        prod_cert, prod_key, _ca = self.nop_pos_config._get_active_nop_cert_material()
        self.assertEqual(prod_cert, self.nop_pos_config.nop_prod_client_cert_pem)
        self.assertEqual(self.nop_pos_config.nop_erp_api_url, "https://api-erp.kverkom.sk")

    def test_mismatched_env_certs_rejected(self):
        other_cert, other_key = _make_self_signed_cert(
            vatsk="9999999999", pokladnica="99999999999999999"
        )
        with self.assertRaises(ValidationError):
            self.nop_pos_config.write({
                "nop_prod_client_cert_pem": base64.b64encode(other_cert),
                "nop_prod_client_key_pem": base64.b64encode(other_key),
            })
