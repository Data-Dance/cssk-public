# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from ..tools.ekasa import (
    EkasaQrError, is_online_qr, parse_fs_datetime, parse_qr,
    payloads_from_printed,
)
from .common import QR_OFFLINE_RESTAURANT, QR_ONLINE_FUEL


class TestEkasaQr(TransactionCase):
    """The QR payloads, pinned to the requests that the service actually
    accepted."""

    def test_online_qr_is_the_identifier_and_nothing_else(self):
        self.assertEqual(parse_qr(QR_ONLINE_FUEL),
                         {"receiptId": "O-ABCDEF0000000002ABCDEF0000000002"})
        self.assertTrue(is_online_qr(QR_ONLINE_FUEL))

    def test_online_qr_is_upper_cased_and_vrp_accepted(self):
        self.assertEqual(parse_qr("o-abcdef0000000002abcdef0000000002"),
                         {"receiptId": "O-ABCDEF0000000002ABCDEF0000000002"})
        self.assertEqual(parse_qr("V-ABCDEF0000000002ABCDEF0000000002"),
                         {"receiptId": "V-ABCDEF0000000002ABCDEF0000000002"})

    def test_offline_qr_becomes_the_composite_key(self):
        """Five fields in, and the numbers must be numbers.

        Sent as strings the service rejects the request; the timestamp has to be
        reformatted from YYMMDDHHMMSS to the service's own dotted form.
        """
        parsed = parse_qr(QR_OFFLINE_RESTAURANT)
        self.assertEqual(parsed, {
            "okp": "AAAA0001-BBBB0002-CCCC0003-DDDD0004-EEEE0005",
            "cashRegisterCode": "88820990000020004",
            "issueDateFormatted": "14.03.2026 19:59:02",
            "receiptNumber": 5,
            "totalAmount": 181.90,
        })
        self.assertIsInstance(parsed["receiptNumber"], int)
        self.assertIsInstance(parsed["totalAmount"], float)
        self.assertFalse(is_online_qr(QR_OFFLINE_RESTAURANT))

    def test_rejects_what_the_service_would_only_reject_later(self):
        for bad in ("",
                    None,
                    "nonsense",
                    "O-NOTHEX",
                    "a:b:c",
                    "OKP:88820000000000001:991399999999:1:2.0",
                    "OKP:88820000000000001:260314195902:five:2.0"):
            with self.assertRaises(EkasaQrError):
                parse_qr(bad)

    def test_fs_datetime(self):
        parsed = parse_fs_datetime("14.03.2026 19:59:02")
        self.assertEqual((parsed.year, parsed.month, parsed.day), (2026, 3, 14))
        self.assertEqual((parsed.hour, parsed.minute, parsed.second), (19, 59, 2))
        self.assertIsNone(parse_fs_datetime(""))
        self.assertIsNone(parse_fs_datetime("2026-03-14"))


class TestEkasaPrinted(TransactionCase):
    """Rebuilding the lookup key from what is printed beside the QR code."""

    def test_a_printed_zero_is_the_letter_o(self):
        """Receipts print the id in a font where O and 0 look alike."""
        self.assertEqual(parse_qr("0-ABCDEF0000000002ABCDEF0000000002"),
                         {"receiptId": "O-ABCDEF0000000002ABCDEF0000000002"})

    def test_offline_identifiers_rebuild_the_composite_key(self):
        """As an AI reading delivers them: OKP wrapped across two lines, the
        number in the till's own "period/number" form, a decimal comma."""
        payloads = payloads_from_printed({
            "okp": "AAAA0001-BBBB0002-CCCC0003-D\nDDD0004-EEEE0005",
            "cash_register_code": "8882 0990 0000 20004",
            "issued_at": "2026-03-14 19:59:02",
            "receipt_number": "202603/5",
            "total": "181,90",
        })
        self.assertEqual(payloads[0], (
            "AAAA0001-BBBB0002-CCCC0003-DDDD0004-EEEE0005"
            ":88820990000020004:260314195902:5:181.90"))
        # The number after the slash is tried first, the whole number second.
        self.assertTrue(payloads[1].endswith(":2026035:181.90"))
        self.assertEqual(len(payloads), 2)
        for payload in payloads:
            parse_qr(payload)

    def test_online_identifier_is_normalised(self):
        self.assertEqual(
            payloads_from_printed({"uid": " 0-abcdef0000000002abcdef0000000002 "}),
            ["O-ABCDEF0000000002ABCDEF0000000002"])

    def test_partial_identifiers_rebuild_nothing(self):
        self.assertEqual(payloads_from_printed({}), [])
        self.assertEqual(payloads_from_printed({"okp": "AAAA0001-BBBB0002"}), [])
        self.assertEqual(payloads_from_printed({"uid": "FIK-1234"}), [])
        self.assertEqual(payloads_from_printed(None), [])
