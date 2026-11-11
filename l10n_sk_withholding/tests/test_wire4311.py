# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Independent FS example, actual remittance and Annex A shape, no filings."""

from copy import deepcopy
from decimal import Decimal
import hashlib
from odoo.tests import BaseCase, tagged
from pathlib import Path
from odoo.tools import file_path

from lxml import etree

from .. import wire4311 as wire


@tagged("post_install", "-at_install")
class TestWithholdingWire(BaseCase):
    def test_birth_number_length_date_checksum_and_payment_boundary(self):
        self.assertEqual(
            wire.checked_birth_number("530101/123", "2026-05-20"), "530101123"
        )
        self.assertEqual(
            wire.checked_birth_number("005101/1235", "2026-05-20"), "0051011235"
        )
        self.assertEqual(
            wire.checked_birth_number("005101123", "2026-05-20"), "005101123"
        )  # 1900, not 2000
        for value in ("540101123", "0051011234", "0013321235", "9999999999"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                wire.checked_birth_number(value, "2026-05-20")
        with self.assertRaisesRegex(ValueError, "precede"):
            wire.checked_birth_number("0051011235", "2000-01-01")

    def author(self):
        item = deepcopy(self.events[0])
        item.update(kind="author", gross="1500", withheld="285", remitted="285")
        item.pop("profit_period_start")
        item.pop("profit_period_end")
        item["recipient"].pop("birth_number")
        return item

    def test_resident_author19_is_in_row01_not_dividend_row_or_annex_a(self):
        result = self.render([self.author()])
        self.schema().assertValid(result)
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01/danZrazena"), "285.00"
        )
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01a/danZrazena"), "0.00"
        )
        self.assertEqual(result.findtext("hlavicka/pocetStrPrilohyA"), "0")
        self.assertFalse(result.xpath("telo/prilohaA"))

    def test_mixed_month_keeps_the_dividend_subset_and_refuses_waiver_double_reporting(
        self,
    ):
        result = self.render(self.events + [self.author()])
        self.schema().assertValid(result)
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01/danZrazena"), "1985.00"
        )
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01a/danZrazena"), "1700.00"
        )
        self.assertEqual(result.findtext("hlavicka/pocetStrPrilohyA"), "1")
        with self.assertRaises(ValueError):
            self.render([dict(self.author(), no_withholding_agreement=True)])

    def setUp(self):
        self.payer = {
            "dic": "2020000000",
            "ico": "36000001",
            "name": "Synthetic dividend payer",
            "street": "Testovacia",
            "number": "1",
            "zip": "85110",
            "city": "Bratislava",
            "country_name": "Slovensko",
            "phone": "+421900000000",
            "prepared_by": "Synthetic operator",
        }
        person = {
            "first_name": "Žofia",
            "last_name": "Šťastná",
            "birth_number": "0051011235",
            "street": "Testovacia",
            "number": "2",
            "zip": "85110",
            "city": "Bratislava",
            "country_name": "Slovensko",
            "country_code": "SK",
        }
        self.events = [
            {
                "person_type": "FO",
                "tax_residence": "SK",
                "recipient": person,
                "gross": gross,
                "profit_period_start": start,
                "profit_period_end": end,
                "paid_on": "2026-05-20",
                "withheld": tax,
                "remitted": tax,
                "remitted_on": "2026-06-15",
            }
            for gross, start, end, tax in [
                ("6500", "2024-01-01", "2024-12-31", "650"),
                ("15000", "2025-01-01", "2025-12-31", "1050"),
            ]
        ]

    def render(self, events=None, **kwargs):
        return etree.fromstring(
            wire.render(
                self.payer,
                "2026-05",
                "2026-06-15",
                self.events if events is None else events,
                **kwargs,
            )
        )

    def schema(self):
        path = Path(file_path("l10n_sk_withholding/data/ozn4311_2026.xsd"))
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(), wire.SCHEMA_SHA256
        )
        return etree.XMLSchema(etree.parse(str(path)))

    def test_fs_6po2026_example_has_1700_and_both_income_records(self):
        result = self.render()
        self.schema().assertValid(result)
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01/danZrazena"), "1700.00"
        )
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01a/danOdvedena"), "1700.00"
        )
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/spolu04/danZrazena"), "1700.00"
        )
        self.assertEqual(result.findtext("hlavicka/pocetStrPrilohyA"), "1")
        incomes = result.xpath("telo/prilohaA/*/udajeOZrazeniAOdvedeni")
        self.assertEqual([row.findtext("sadzbaDane") for row in incomes], ["10", "7"])
        self.assertEqual(
            [row.findtext("sumaZdanPrijmu") for row in incomes], ["6500.00", "15000.00"]
        )

    def test_actual_unremitted_tax_is_not_reported_as_paid(self):
        events = deepcopy(self.events)
        events[0].update(remitted="0", remitted_on=None)
        result = self.render(events)
        self.schema().assertValid(result)
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01/danZrazena"), "1700.00"
        )
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/zPrijmDan01/danOdvedena"), "1050.00"
        )
        self.assertIn(
            result.findtext(
                "telo/prilohaA/udajeA_1/udajeOZrazeniAOdvedeni/datumOdvedenia"
            ),
            ("", None),
        )

    def test_three_income_records_use_two_pages_and_a_required_empty_second_slot(self):
        result = self.render(self.events + [deepcopy(self.events[0])])
        self.schema().assertValid(result)
        self.assertEqual(result.findtext("hlavicka/pocetStrPrilohyA"), "2")
        self.assertEqual(
            result.xpath("telo/prilohaA/strana/aktualna/text()"), ["1", "2"]
        )
        self.assertEqual(
            result.xpath("telo/prilohaA/strana/celkovo/text()"), ["2", "2"]
        )
        self.assertEqual(len(result.xpath("telo/prilohaA/udajeA_2")), 2)

    def test_correction_is_complete_replacement_including_annex(self):
        result = self.render(original_filed_on="2026-06-10")
        self.schema().assertValid(result)
        self.assertEqual(result.findtext("hlavicka/dovodDoplnenia"), "1")
        self.assertEqual(result.findtext("hlavicka/datumPovodne"), "10.06.2026")
        self.assertEqual(
            result.findtext("hlavicka/suhrnneUdaje/spolu04/danZrazena"), "1700.00"
        )
        self.assertEqual(len(result.xpath("telo/prilohaA")), 1)

    def test_mathematical_cent_rounding_section47_not_floor_or_bankers_rounding(self):
        # FS: from2020, withholding tax is mathematically rounded to cents.
        self.assertEqual(
            wire.dividend_tax("10.05", "2024-01-01"), (Decimal("10"), Decimal("1.01"))
        )
        self.assertEqual(
            wire.dividend_tax("10.50", "2025-01-01"), (Decimal("7"), Decimal("0.74"))
        )
        self.assertEqual(wire.dividend_tax("9500", "2025-01-01")[1], Decimal("665"))
        self.assertEqual(wire.dividend_tax("1000", "2024-06-01")[1], Decimal("100"))

    def test_no_assigned_slovak_rc_uses_actual_birth_date(self):
        events = deepcopy(self.events[:1])
        events[0]["recipient"].update(birth_number=None, birth_date="1985-01-01")
        result = self.render(events)
        self.schema().assertValid(result)
        self.assertEqual(
            result.findtext("telo/prilohaA/udajeA_1/datumNarodenia"), "01.01.1985"
        )

    def test_schema_valid_empty_body_is_legally_incomplete_and_is_not_accepted(self):
        result = self.render()
        body = result.find("telo")
        for node in list(body):
            body.remove(node)
        # XSD permits omission; the application must not infer legal optionality.
        self.schema().assertValid(result)
        with self.assertRaises(ValueError):
            self.render([])

    def test_wrong_vintage_dates_amounts_residency_and_identity_do_not_silently_file(
        self,
    ):
        for changes in (
            {"withheld": "649.99"},
            {"remitted": "651"},
            {"remitted_on": "2026-06-16"},
            {"paid_on": "2026-06-01"},
            {"tax_residence": "CZ"},
            {"person_type": "PO"},
            {"gross": "NaN"},
            {"gross": "-1"},
            {"gross": "1.001"},
            {"profit_period_start": "2016-01-01"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.render([dict(self.events[0], **changes)])
        for person in ({"birth_number": "", "birth_date": None}, {"first_name": ""}):
            events = deepcopy(self.events[:1])
            events[0]["recipient"].update(person)
            with self.assertRaises(ValueError):
                self.render(events)
