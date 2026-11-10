# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Wire assertions against the published VszP 2023 interface table."""

from copy import deepcopy
from odoo.tests import BaseCase, tagged

from .. import text514 as codec


@tagged("post_install", "-at_install")
class TestHealthTextCodec(BaseCase):
    def test_different_hr_rows_must_not_duplicate_one_insured_person(self):
        # An employee record is not the insurer's person identity: two
        # concurrent jobs may have separate HR cards but the same RC.
        self.rows.append(deepcopy(self.rows[0]))
        with self.assertRaises(ValueError):
            codec.render(self.ident, self.employer, self.summary, self.rows)

    def setUp(self):
        super().setUp()
        self.ident = {
            "characteristic": "N",
            "ico": "36000001",
            "payer": "1234567890",
            "insurer": "2500",
            "sent_on": "2026-07-01",
            "sequence": 1,
        }
        self.employer = {
            "period": "202606",
            "payment_day": 15,
            "name": "Syntetická spoločnosť",
            "dic": "2023456787",
            "iban": "SK3112000000198742637541",
            "legal_form": "PO",
        }
        self.summary = {
            "registered": 1,
            "count_standard": 1,
            "count_disabled": 0,
            "days_standard": 30,
            "days_disabled": 0,
            "rate_er_standard": 11,
            "rate_ee_standard": 5,
            "rate_er_disabled": None,
            "rate_ee_disabled": None,
            "income_standard": 500,
            "income_disabled": 0,
            "base_standard": 500,
            "base_disabled": 0,
            "er_standard": 55,
            "ee_standard": 25,
            "er_disabled": 0,
            "ee_disabled": 0,
            "total": 80,
            "registered_all_insurers": 1,
        }
        self.rows = [
            {
                "birth_number": "9001010007",
                "days": 30,
                "rate_employer": 11,
                "rate_employee": 5,
                "income": 500,
                "base": 500,
                "employer": 55,
                "employee": 25,
                "total": 80,
                "op_income": 0,
                "other_income": 500,
                "op": 0,
                "exempt_income": 0,
                "shorttime_base": None,
                "minimum_opt_out": 0,
                "topup": 0,
                "disabled": False,
                "premium_assessed": True,
            }
        ]

    def render(self):
        return codec.render(self.ident, self.employer, self.summary, self.rows)

    def test_exact_independent_reference_bytes_and_filename(self):
        expected = (
            "N|514|36000001|1234567890|2500|20260701|1|1|1|1|\r\n"
            "202606|15|Syntetická spoločnosť|36000001|1234567890|2023456787|||||||SK3112000000198742637541|\r\n"
            "1|11,00|5,00|||1|0|30|0|500,00|0,00|500,00|0,00|55,00|25,00|0,00|0,00|80,00|PO|1|\r\n"
            "1|9001010007|30|11,00|5,00|500,00|500,00|55,00|25,00|80,00|0,00|500,00|0,00|0,00||0|0,00|\r\n"
        ).encode("utf-8")
        self.assertEqual(self.render(), expected)
        self.assertEqual(codec.filename("N", "202606", 1), "N5142606.001")
        records = self.render().decode().splitlines()
        self.assertEqual(
            [len(record.split("|")) - 1 for record in records], [10, 13, 20, 17]
        )

    def test_all_insurers_characteristics_and_original_birth_digits(self):
        for insurer in ("2400", "2500", "2700"):
            for characteristic in ("N", "O", "A"):
                with self.subTest(insurer=insurer, characteristic=characteristic):
                    self.ident.update(insurer=insurer, characteristic=characteristic)
                    self.rows[0]["birth_number"] = "001010123"
                    self.assertIn(b"|001010123|", self.render())
                    self.assertTrue(
                        self.render().startswith((characteristic + "|514|").encode())
                    )

    def test_totals_minimum_optout_and_record_injection_are_rejected(self):
        self.rows[0]["total"] = 81
        with self.assertRaises(ValueError):
            self.render()
        self.rows[0].update(total=81, topup=1, minimum_opt_out=1)
        with self.assertRaises(ValueError):
            self.render()
        self.rows[0].update(total=80, topup=0, minimum_opt_out=0)
        self.employer["name"] = "Bad|record"
        with self.assertRaises(ValueError):
            self.render()

    def test_invalid_precision_dates_and_iban_do_not_silently_change(self):
        self.assertEqual(codec.money("-0.00"), "0,00")
        for amount in ("0.001", "NaN", "Infinity"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                codec.money(amount)
        self.employer["period"] = "202212"
        with self.assertRaises(ValueError):
            self.render()

    def test_both_groups_and_topup_are_in_their_published_columns(self):
        self.rows[0].update(
            income=100,
            base=100,
            employer=11,
            employee=5,
            topup="29.45",
            total="45.45",
            other_income=100,
        )
        disabled = deepcopy(self.rows[0])
        disabled.update(
            birth_number="0051010008",
            disabled=True,
            income=1000,
            base=1000,
            other_income=1000,
            rate_employer="5.5",
            rate_employee="2.5",
            employer=55,
            employee=25,
            topup=0,
            total=80,
        )
        self.rows.append(disabled)
        self.summary = codec.aggregate(
            self.rows, registered=2, registered_all_insurers=3
        )
        records = [line.split("|")[:-1] for line in self.render().decode().splitlines()]
        self.assertEqual(
            records[2],
            [
                "2",
                "11,00",
                "5,00",
                "5,50",
                "2,50",
                "1",
                "1",
                "30",
                "30",
                "100,00",
                "1000,00",
                "100,00",
                "1000,00",
                "11,00",
                "34,45",
                "55,00",
                "25,00",
                "125,45",
                "PO",
                "3",
            ],
        )
        self.assertEqual(records[3][8:10], ["5,00", "45,45"])
        self.assertEqual(records[3][15:17], ["0", "29,45"])
        self.assertEqual(records[4][3:5], ["5,50", "2,50"])

    def test_registered_whole_month_sick_person_is_not_a_paid_person(self):
        self.rows[0].update(
            days=0,
            income=0,
            base=0,
            employer=0,
            employee=0,
            total=0,
            other_income=0,
            premium_assessed=False,
        )
        self.summary = codec.aggregate(
            self.rows, registered=1, registered_all_insurers=1
        )
        values = self.render().decode().splitlines()[2].split("|")
        self.assertEqual(values[0], "1")
        self.assertEqual(values[5:9], ["0", "0", "0", "0"])
        self.assertEqual(values[17], "0,00")

    def test_deductible_allowance_and_shorttime_do_not_change_source_money(self):
        self.rows[0].update(
            op_income=420,
            other_income=0,
            income=420,
            op=300,
            base=120,
            employer="46.20",
            employee=6,
            total="52.20",
        )
        self.summary = codec.aggregate(
            self.rows, registered=1, registered_all_insurers=1
        )
        values = self.render().decode().splitlines()[3].split("|")
        self.assertEqual(values[5:10], ["420,00", "120,00", "46,20", "6,00", "52,20"])
        self.assertEqual(values[10:13], ["420,00", "0,00", "300,00"])
        # Employer exemption during short-time support changes its own base;
        # it must not overwrite the employee income or employee base.
        self.rows[0].update(shorttime_base=200, employer=22, total=28)
        self.summary = codec.aggregate(
            self.rows, registered=1, registered_all_insurers=1
        )
        records = [line.split("|") for line in self.render().decode().splitlines()]
        self.assertEqual(records[2][9], "200,00")
        self.assertEqual(records[2][11], "120,00")
        self.assertEqual(records[3][5], "420,00")
        self.assertEqual(records[3][14], "200,00")

    def test_optout_does_not_mean_disability_or_state_insurance(self):
        self.rows[0]["minimum_opt_out"] = 1
        self.assertIn(b"||1|0,00|\r\n", self.render())
        self.rows[0]["minimum_opt_out"] = True
        with self.assertRaises(ValueError):
            self.render()

    def test_additive_negative_premiums_are_not_turned_positive(self):
        self.ident["characteristic"] = "A"
        self.rows[0].update(
            income=-500,
            base=-500,
            other_income=-500,
            employer=-55,
            employee=-25,
            total=-80,
            days=0,
        )
        self.summary = codec.aggregate(
            self.rows, registered=1, registered_all_insurers=1
        )
        self.assertIn(b"|-500,00|-500,00|-55,00|-25,00|-80,00|", self.render())

    def test_rate_conflict_and_unknown_source_group_are_not_guessed(self):
        other = deepcopy(self.rows[0])
        other["rate_employee"] = 4
        with self.assertRaises(ValueError):
            codec.aggregate(self.rows + [other], 2, 2)
        for key in ("disabled", "premium_assessed"):
            row = deepcopy(self.rows[0])
            row[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                codec.aggregate([row], 1, 1)

    def test_real_month_boundaries_and_filenames(self):
        self.employer["period"] = "202602"
        with self.assertRaises(ValueError):
            self.render()
        self.rows[0]["days"] = 28
        self.render()
        self.employer["period"] = "202402"
        self.rows[0]["days"] = 29
        self.render()
        for period, sequence in [
            ("202613", 1),
            ("202212", 1),
            ("202606", 1000),
            ("202606", 1.5),
            ("202606", True),
        ]:
            with (
                self.subTest(period=period, sequence=sequence),
                self.assertRaises(ValueError),
            ):
                codec.filename("N", period, sequence)
        self.employer["period"] = "202606"
        self.employer["iban"] = "SK0012000000198742637541"
        with self.assertRaises(ValueError):
            self.render()
