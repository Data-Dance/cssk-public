from odoo.tests import tagged

from .common import NopBaseCase


@tagged("post_install", "-at_install")
class TestIntegrityHash(NopBaseCase):
    """SHA-256 of ``IBAN|AMOUNT|EUR|endToEndId`` — the canonical SBA integrity hash."""

    def test_hash_matches_sba_format(self):
        """Known-answer test using the pipe-separated UTF-8 concatenation."""
        import hashlib
        iban = "SK3112000000198742637541"
        amount = 123.45
        end_to_end = "QR-e22732a02dca40ed8d850b0e38ed130e"
        expected = hashlib.sha256(
            f"{iban}|{amount:.2f}|EUR|{end_to_end}".encode("utf-8")
        ).hexdigest()
        actual = self.env["nop.transaction"]._compute_integrity_hash(
            iban, amount, end_to_end
        )
        self.assertEqual(actual, expected)

    def test_hash_is_lowercase_hex(self):
        digest = self.env["nop.transaction"]._compute_integrity_hash(
            "SK00", 1.0, "QR-x"
        )
        self.assertEqual(digest, digest.lower())
        self.assertEqual(len(digest), 64)
        int(digest, 16)  # must be hex

    def test_hash_amount_formatting(self):
        """Integer amount 10 must format as '10.00' per SBA standard."""
        hash_int = self.env["nop.transaction"]._compute_integrity_hash("SK1", 10, "QR-a")
        hash_str = self.env["nop.transaction"]._compute_integrity_hash("SK1", "10.00", "QR-a")
        self.assertEqual(hash_int, hash_str)
