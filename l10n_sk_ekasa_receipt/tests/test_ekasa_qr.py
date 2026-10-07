# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from ..tools.ekasa import EkasaQrError, is_online_qr, parse_fs_datetime, parse_qr
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
