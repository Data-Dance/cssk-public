"""Shared test helpers for the NOP KVERKOM modules.

A disposable self-signed X.509 certificate is generated in :meth:`setUpClass`
with a subject matching the format the parser expects.
"""

import base64
from datetime import datetime, timedelta

from odoo.tests import TransactionCase

TEST_VATSK = "1234567890"
TEST_POKLADNICA = "88812345678900001"
TEST_IBAN = "SK3112000000198742637541"


def _make_self_signed_cert(vatsk=TEST_VATSK, pokladnica=TEST_POKLADNICA):
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "SK"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, pokladnica),
        x509.NameAttribute(
            NameOID.COMMON_NAME, f"VATSK-{vatsk} POKLADNICA {pokladnica}"
        ),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow() - timedelta(minutes=1))
        .not_valid_after(datetime.utcnow() + timedelta(days=1))
        .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return cert_pem, key_pem


class NopBaseCase(TransactionCase):
    """Base class that provisions a pos.config with NOP cert + IBAN."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        cls.company = cls.env.company

        cls.bank = cls.env["res.partner.bank"].search([
            ("sanitized_acc_number", "=", TEST_IBAN.replace(" ", "")),
            ("partner_id", "=", cls.company.partner_id.id),
        ], limit=1) or cls.env["res.partner.bank"].create({
            "acc_number": TEST_IBAN,
            "partner_id": cls.company.partner_id.id,
            "acc_holder_name": "Test Merchant",
        })

        cert_pem, key_pem = _make_self_signed_cert()
        nop_vals = {
            "nop_environment": "int",
            "nop_iban_id": cls.bank.id,
            "nop_merchant_name": "Test Merchant",
            "nop_int_client_cert_pem": base64.b64encode(cert_pem),
            "nop_int_client_cert_filename": "cert.pem",
            "nop_int_client_key_pem": base64.b64encode(key_pem),
            "nop_int_client_key_filename": "key.pem",
        }

        # Re-use an existing NOP-configured pos.config if one exists for
        # this VATSK/POKLADNICA, so the unique constraint doesn't block tests
        # that run on a DB with bootstrap data.
        existing = cls.env["pos.config"].search([
            ("nop_vatsk", "=", TEST_VATSK),
            ("nop_pokladnica_id_ext", "=", TEST_POKLADNICA),
            ("nop_environment", "=", "int"),
        ], limit=1)
        if existing:
            existing.write(nop_vals)
            cls.nop_pos_config = existing
        else:
            cls.nop_pos_config = cls.env["pos.config"].create({
                "name": "NOP Test POS",
                "payment_method_ids": [(6, 0, [])],
                **nop_vals,
            })

    @classmethod
    def _build_notification(
        cls, transaction_id, amount, iban=TEST_IBAN, currency="EUR", corrupt_hash=False
    ):
        integrity = cls.env["nop.transaction"]._compute_integrity_hash(
            iban, amount, transaction_id, currency=currency
        )
        if corrupt_hash:
            integrity = "0" * 64
        return {
            "transactionStatus": "ACCC",
            "transactionAmount": {"currency": currency, "amount": f"{amount:.2f}"},
            "endToEndId": transaction_id,
            "dataIntegrityHash": integrity,
            "creditorAccount": {"iban": iban},
            "creditorName": "Test Merchant",
            "receivedAt": datetime.utcnow().isoformat() + "Z",
        }
