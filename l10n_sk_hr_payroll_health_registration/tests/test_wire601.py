# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from copy import deepcopy
import hashlib
from pathlib import Path

from lxml import etree
from odoo.tests import BaseCase, tagged

from .. import wire601


@tagged("post_install", "-at_install")
class TestHealthRegistrationWire(BaseCase):
    def setUp(self):
        super().setUp()
        self.ident = {
            "characteristic": "N",
            "sender": "36000001",
            "receiver": "12345678",
            "insurer": "2500",
            "sent_on": "2026-07-01",
            "sequence": 1,
        }
        self.payer = {
            "payer": "9900112233",
            "period": "2026-06",
            "name": "Syntetická spoločnosť",
            "ico": "36000001",
            "legal_form": "PO",
            "town": "Bratislava",
            "street": "Testovacia1",
            "postcode": "85110",
            "phone": "+421900000000",
            "responsible_person": "Syntetická osoba",
            "iban": "SK3112000000198742637541",
        }
        self.events = [
            {
                "birth_number": "005101123",
                "first_name": "Žofia",
                "last_name": "Šťastná",
                "code": "2D",
                "validity": "Z",
                "changed_on": "2026-06-02",
            },
            {
                "birth_number": "005101123",
                "first_name": "Žofia",
                "last_name": "Šťastná",
                "code": "2D",
                "validity": "K",
                "changed_on": "2026-06-02",
            },
        ]

    def schema(self):
        source = Path(__file__).parents[1] / "schemas" / "davka601-derived-2026.xsd"
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(), wire601.SCHEMA_SHA256
        )
        return etree.XMLSchema(etree.parse(str(source)))

    def test_exact_text_fields_encoding_dates_and_trailing_delimiters(self):
        result = wire601.render_text(self.ident, self.payer, self.events)
        self.assertTrue(result.endswith(b"|\r\n"))
        self.assertNotIn(b"\xc5\xbd", result)
        rows = [row.split("|")[:-1] for row in result.decode("iso8859-2").splitlines()]
        self.assertEqual([len(row) for row in rows], [10, 25, 9, 9])
        self.assertEqual(
            rows[0],
            [
                "N",
                "601",
                "36000001",
                "12345678",
                "2500",
                "20260701",
                "1",
                "2",
                "1",
                "1",
            ],
        )
        self.assertEqual(rows[1][3:5], ["06", "26"])
        self.assertEqual(
            rows[2],
            ["1", "005101123", "", "Žofia", "Šťastná", "2D", "Z", "20260602", ""],
        )
        self.assertEqual(rows[3][5:8], ["2D", "K", "20260602"])
        self.assertEqual(wire601.filename(self.ident), "36000001260701.601")

    def test_xml_matches_the_pinned_derived_schema_and_the_same_facts(self):
        result = wire601.render_xml(self.ident, self.payer, self.events)
        root = etree.fromstring(result)
        self.schema().assertValid(root)
        self.assertEqual(
            root.xpath("PersonData/DateOfChange/text()"), ["20260602", "20260602"]
        )
        self.assertEqual(
            root.xpath("PersonData/IdentificationNumberOfInsured/text()"),
            ["005101123"] * 2,
        )

    def test_all_insurers_and_both_batch_characteristics_keep_event_validity_separate(
        self,
    ):
        for insurer in ("2400", "2500", "2700"):
            for characteristic in ("N", "O"):
                ident = dict(self.ident, insurer=insurer, characteristic=characteristic)
                records = wire601.records(ident, self.payer, self.events)
                self.assertEqual(records[0][0], characteristic)
                self.assertEqual(records[1][1:3], [insurer[:2], "00"])
                self.assertEqual(records[2][0][6], "Z")

    def test_assigned_bic_is_an_alternative_to_rc_and_is_not_fabricated(self):
        event = dict(
            self.events[0], birth_number=False, insurer_identifier="1273452026"
        )
        root = etree.fromstring(wire601.render_xml(self.ident, self.payer, [event]))
        self.schema().assertValid(root)
        self.assertEqual(
            root.findtext("PersonData/NonSemanticIdentificationNumber"), "1273452026"
        )
        for changes in ({"birth_number": "005101123"}, {"insurer_identifier": False}):
            with self.assertRaises(ValueError):
                wire601.records(self.ident, self.payer, [dict(event, **changes)])

    def test_unicode_names_are_lossless_in_xml_and_rejected_for_latin2_text(self):
        events = [dict(self.events[0], first_name="李", last_name="王")]
        root = etree.fromstring(wire601.render_xml(self.ident, self.payer, events))
        self.schema().assertValid(root)
        self.assertEqual(root.findtext("PersonData/Name"), "李")
        with self.assertRaises(ValueError):
            wire601.render_text(self.ident, self.payer, events)

    def test_optional_national_bank_fields_are_not_required_instead_of_iban(self):
        self.schema().assertValid(
            etree.fromstring(wire601.render_xml(self.ident, self.payer, self.events))
        )
        for changes in (
            {"iban": "SK0012000000198742637541"},
            {"iban": ""},
            {"phone": ""},
        ):
            with self.assertRaises(ValueError):
                wire601.records(self.ident, dict(self.payer, **changes), self.events)

    def test_input_injection_overlong_names_and_invalid_calendar_dates_are_rejected(
        self,
    ):
        for changes in (
            {"first_name": "Name|extra"},
            {"last_name": "Name\r\nextra"},
            {"first_name": "a" * 25},
            {"title": "Dr"},
            {"changed_on": "2026-02-29"},
            {"changed_on": "2026-W23-2"},
            {"code": "2X"},
            {"validity": "A"},
        ):
            with self.assertRaises(ValueError):
                wire601.render_text(
                    self.ident, self.payer, [dict(self.events[0], **changes)]
                )

    def test_duplicate_events_reject_but_same_day_start_end_is_valid(self):
        wire601.records(self.ident, self.payer, self.events)
        with self.assertRaises(ValueError):
            wire601.records(
                self.ident, self.payer, [self.events[0], deepcopy(self.events[0])]
            )

    def test_cancel_rows_preserve_the_reviewed_code_and_exact_date(self):
        event = dict(self.events[0], validity="X")
        rows = wire601.records(self.ident, self.payer, [event])[2]
        self.assertEqual(rows[0][5:8], ["2D", "X", "20260602"])

    def test_2s_published_schema_defect_is_not_silently_repaired(self):
        schema = self.schema()
        schema.assertValid(
            etree.fromstring(wire601.render_xml(self.ident, self.payer, self.events))
        )
        event = dict(self.events[0], code="2S")
        self.assertIn(b"|2S|", wire601.render_text(self.ident, self.payer, [event]))
        root = etree.fromstring(wire601.render_xml(self.ident, self.payer, [event]))
        # The published pattern asks for trailing spaces after2S, which the
        # table's1–2 character code cannot contain. Keep that fact visible.
        self.assertFalse(schema.validate(root))
        self.assertTrue(
            any("CodeOfChange" in error.message for error in schema.error_log)
        )
