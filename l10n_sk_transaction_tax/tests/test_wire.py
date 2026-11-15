"""Official DFT formula/format controls; not native accounting acceptance."""

from copy import deepcopy
from decimal import Decimal
import hashlib
import re
from odoo.tests import BaseCase, tagged
from pathlib import Path
from odoo.tools import file_path

from lxml import etree

from .. import wire

root = Path(file_path("l10n_sk_transaction_tax"))


@tagged("post_install", "-at_install")
class TestDftSchemaPins(BaseCase):
    def test_bundled_bytes_match_pins_and_no_schema_is_unpinned(self):
        entries = re.findall(
            r"^(\S+\.xsd)\s+([a-f0-9]{32})\s+(\d+)$",
            (root / "data/SCHEMA_VERSION").read_text(),
            re.M,
        )
        self.assertTrue(entries)
        self.assertEqual(
            {name for name, _, _ in entries},
            {path.name for path in (root / "data").glob("*.xsd")},
        )
        for name, digest, size in entries:
            content = (root / "data" / name).read_bytes()
            self.assertEqual(
                (hashlib.md5(content).hexdigest(), len(content)), (digest, int(size))
            )


@tagged("post_install", "-at_install")
class TestDftWire(BaseCase):
    def setUp(self):
        self.payer = {
            "ico": "36000001",
            "dic": "2020000000",
            "name": "Synthetic corporate DFT payer",
            "city": "Bratislava",
            "zip": "85110",
            "country_name": "Slovensko",
            "street": "Testovacia",
            "number": "1",
        }
        self.person = {
            "kind": "statutarnyZastupcaPO",
            "first_name": "Syntetická",
            "last_name": "Osoba",
        }

    def row(self, key="T1", kind="transfer", base="1000", **values):
        return {
            "transaction_key": key,
            "kind": kind,
            "base_eur": base,
            "actual_on": "2026-05-20",
            "source_reference": "Synthetic reviewed bank/settlement source",
            "reviewed": True,
            **values,
        }

    def render(self, rows=None, **values):
        options = {"grounds": {"c"}, "representative": self.person, **values}
        result = etree.fromstring(
            wire.render(
                self.payer,
                "2026-05",
                [self.row()] if rows is None else rows,
                "2026-06-30",
                **options,
            )
        )
        schema = root / "data/ozndft_2026.xsd"
        self.assertEqual(
            hashlib.sha256(schema.read_bytes()).hexdigest(), wire.SCHEMA_SHA256
        )
        etree.XMLSchema(etree.parse(str(schema))).assertValid(result)
        return result

    def test_one_transfer_cap_is_not_a_monthly_cap(self):
        single = self.render([self.row(base="30000")])
        split = self.render(
            [self.row("T1", base="15000"), self.row("T2", base="15000")]
        )
        self.assertEqual(single.findtext("telo/r1s2"), "40.00")
        self.assertEqual(split.findtext("telo/r1s1"), "30000.00")
        self.assertEqual(split.findtext("telo/r1s2"), "80.00")

    def test_cash_is_not_capped_at_40(self):
        result = self.render([self.row(kind="cash", base="50000")])
        self.assertEqual(result.findtext("telo/r2s2"), "400.00")
        self.assertEqual(result.findtext("telo/r7"), "400.00")

    def test_minimum_cent_zero_and_half_cent(self):
        self.assertEqual(wire.transaction_tax("0.01", "transfer"), Decimal(".01"))
        self.assertEqual(wire.transaction_tax("0", "transfer"), 0)
        self.assertEqual(wire.transaction_tax("3.75", "transfer"), Decimal(".02"))
        self.assertEqual(wire.transaction_tax("3.74", "transfer"), Decimal(".01"))

    def test_fx_base_is_not_rounded_before_tax_but_form_displays_cents(self):
        result = self.render([self.row(base="3.749")])
        self.assertEqual(result.findtext("telo/r1s1"), "3.75")
        self.assertEqual(result.findtext("telo/r1s2"), "0.01")

    def test_unknown_recharge_has_no_40_cap_known_original_has_cap(self):
        unknown = self.render(
            [self.row(kind="recharge_unknown", base="300000")], grounds={"d"}
        )
        known = self.render(
            [self.row(kind="recharge_known", base="300000")], grounds={"d"}
        )
        self.assertEqual(unknown.findtext("telo/r4s2"), "1200.00")
        self.assertEqual(known.findtext("telo/r5s2"), "40.00")

    def test_reviewed_section10_reductions_can_produce_a_negative_total(self):
        result = self.render(
            [self.row(kind="recharge_known", base="300000")],
            grounds={"d"},
            adjustments=[
                {
                    "amount": "-80",
                    "source_reference": "Synthetic actual proportional tax deductions",
                    "reviewed": True,
                }
            ],
            refund={
                "requested": True,
                "iban": "SK3112000000198742637541",
                "date": "2026-06-30",
            },
        )
        self.assertEqual(result.findtext("telo/r6"), "-80.00")
        self.assertEqual(result.findtext("telo/r7"), "-40.00")
        self.assertEqual(result.findtext("telo/vratenieDane/ziadamVratenie"), "1")

    def test_bank_collected_and_exempt_sources_are_retained_but_not_taxed_twice(self):
        rows = [
            self.row(
                "B1",
                "bank_collected",
                classification_reference="Synthetic bank tax debit",
            ),
            self.row(
                "E1",
                "excluded",
                classification_reference="Synthetic reviewed section 4 exclusion",
            ),
        ]
        values, facts = wire.calculate(rows, "2026-05")
        self.assertEqual(values["r7"], 0)
        self.assertEqual(len(facts), 2)
        self.assertEqual(self.render(rows).findtext("telo/r7"), "0.00")

    def test_used_card_tax_is_annual_and_in_december(self):
        rows = [
            self.row(
                "C1",
                "card",
                card_reference="Synthetic-card-one",
                actual_on="2026-03-10",
            ),
            self.row(
                "C2",
                "card",
                card_reference="Synthetic-card-two",
                actual_on="2026-11-10",
            ),
        ]
        values, _ = wire.calculate(rows, "2026-12")
        self.assertEqual((values["r3s1"], values["r3s2"]), (2, 4))
        with self.assertRaises(ValueError):
            wire.calculate(rows, "2026-05")
        rows[1]["card_reference"] = rows[0]["card_reference"]
        with self.assertRaises(ValueError):
            wire.calculate(rows, "2026-12")

    def test_complete_correction_keeps_full_tax_rows(self):
        result = self.render(filing_type="corrective")
        self.assertEqual(result.findtext("hlavicka/typDP/odp"), "1")
        self.assertEqual(result.findtext("telo/r7"), "4.00")
        self.assertIn(result.findtext("telo/r9"), ("", None))

    def test_additional_has_last_known_tax_and_signed_difference(self):
        result = self.render(
            filing_type="additional",
            discovered_on="2026-06-20",
            previous_tax="12",
            refund={
                "requested": True,
                "foreign_account_details": "Synthetic nonIBAN account and bank BIC/address",
                "date": "2026-06-30",
            },
        )
        self.assertEqual(result.findtext("telo/r8"), "12.00")
        self.assertEqual(result.findtext("telo/r9"), "-8.00")
        self.assertEqual(result.findtext("hlavicka/typDP/datumDDP"), "20.06.2026")

    def test_incomplete_or_wrong_month_sources_are_not_silently_accepted(self):
        for changes in (
            {"actual_on": "2026-06-01"},
            {"reviewed": False},
            {"source_reference": ""},
            {"base_eur": "NaN"},
            {"base_eur": "-1"},
            {"transaction_key": False},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.render([self.row(**changes)])
        with self.assertRaises(ValueError):
            self.render([self.row(), deepcopy(self.row())])

    def test_wrong_payer_roles_adjustments_and_refund_require_evidence(self):
        for values in (
            {"grounds": {"a"}},
            {"grounds": set()},
            {"representative": {}},
            {"previous_tax": 1},
            {"filing_type": "additional"},
            {"refund": {"requested": True}},
            {
                "adjustments": [
                    {
                        "amount": "-1",
                        "source_reference": "Unreviewed",
                        "reviewed": False,
                    }
                ]
            },
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.render(**values)

    def test_split_identified_recharge_uses_one_transaction_cap(self):
        rows = [
            self.row(kind="recharge_known", base="15000"),
            self.row(kind="recharge_known", base="15000"),
        ]
        root = self.render(rows, grounds={"d"})
        self.assertEqual(root.findtext("telo/r5s1"), "30000.00")
        self.assertEqual(root.findtext("telo/r5s2"), "40.00")

    def test_identified_recharge_uses_only_the_remaining_historical_tax_cap(self):
        history = [
            {
                "transaction_key": "T1",
                "kind": "recharge_known",
                "base_eur": "5000",
                "tax": "20.00",
            }
        ]
        root = self.render(
            [self.row(kind="recharge_known", base="20000")],
            grounds={"d"},
            recharge_history=history,
        )
        self.assertEqual(root.findtext("telo/r5s1"), "20000.00")
        self.assertEqual(root.findtext("telo/r5s2"), "20.00")
        for changed in ({"tax": "40.00"}, {"kind": "recharge_unknown"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.render(
                    [self.row(kind="recharge_known", base="20000")],
                    grounds={"d"},
                    recharge_history=[{**history[0], **changed}],
                )

    def test_excluded_recharge_retains_payment_and_classification_without_tax(self):
        root = self.render(
            [
                self.row(
                    kind="recharge_excluded",
                    base="30000",
                    classification_reference="Reviewed original transfer outside the tax object",
                )
            ],
            grounds={"d"},
        )
        self.assertEqual(root.findtext("telo/r7"), "0.00")

    def test_partial_month_keeps_month_year_and_exact_dates(self):
        root = self.render(period_from="2026-05-10", period_to="2026-05-25")
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/mesiac"), "5")
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/rok"), "2026")
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/od"), "10.05.2026")
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/do"), "25.05.2026")

    def test_partial_month_rejects_missing_reversed_foreign_month_and_outside_sources(
        self,
    ):
        for values in (
            {"period_from": "2026-05-10"},
            {"period_from": "2026-05-25", "period_to": "2026-05-10"},
            {"period_from": "2026-04-30", "period_to": "2026-05-25"},
            {"period_from": "2026-05-10", "period_to": "2026-06-01"},
            {"period_from": "2026-05-20", "period_to": "2026-05-20"},
            {"period_from": "2026-05-21", "period_to": "2026-05-25"},
        ):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.render(**values)

    def test_refund_destination_is_not_both_iban_and_foreign_details(self):
        with self.assertRaisesRegex(ValueError, "not both"):
            self.render(
                adjustments=[
                    {
                        "amount": "-10",
                        "reviewed": True,
                        "source_reference": "Reviewed previous tax source",
                    }
                ],
                refund={
                    "requested": True,
                    "iban": "SK3112000000198742637541",
                    "foreign_account_details": "Another account",
                    "date": "2026-06-30",
                },
            )
