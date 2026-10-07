# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_cssk_receipt_capture.tools.amounts import flatten_label

from ..tools.ekasa import map_receipt
from .common import load_fixture


class TestEkasaMapping(TransactionCase):
    """Mapping, against two responses from Finančná správa.

    Every assertion here corresponds to a way of getting it wrong that these
    two receipts actually expose.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fuel_payload = load_fixture("receipt_online_fuel.json")
        cls.rest_payload = load_fixture("receipt_offline_restaurant.json")
        cls.fuel = map_receipt(cls.fuel_payload, flatten=flatten_label)
        cls.rest = map_receipt(cls.rest_payload, flatten=flatten_label)

    # ------------------------------------------------------------------
    # the VAT recap
    # ------------------------------------------------------------------
    def test_recap_comes_from_vat_summary_not_the_legacy_pair(self):
        """The restaurant payload carries both, and they disagree.

        ``vatRateBasic`` says 20 and ``vatRateReduced`` says 10 — stale labels
        from the regime before 2025 — while the items and ``vatSummary`` say
        23, 19 and 5. Reading the legacy pair would post 20 % tax on a 23 %
        purchase.
        """
        self.assertEqual(self.rest_payload["receipt"]["vatRateBasic"], 20.0)
        self.assertEqual(self.rest_payload["receipt"]["vatRateReduced"], 10.0)
        rates = sorted(t["vat_rate"] for t in self.rest["taxes"])
        self.assertEqual(rates, [5.0, 19.0, 23.0])
        self.assertNotIn(20.0, rates)
        self.assertNotIn(10.0, rates)
        self.assertIsNone(self.rest["warning"])

    def test_recap_survives_a_null_legacy_pair(self):
        """On the fuel payload the entire legacy pair is null."""
        receipt = self.fuel_payload["receipt"]
        self.assertIsNone(receipt["vatRateBasic"])
        self.assertIsNone(receipt["taxBaseBasic"])
        self.assertIsNone(receipt["vatAmountReduced"])
        self.assertEqual(self.fuel["taxes"], [
            {"vat_rate": 23.0, "amount_untaxed": 47.03, "amount_tax": 10.82}])

    def test_without_a_summary_the_recap_is_derived_from_the_items(self):
        """Not from the legacy pair, which has two slots and stale labels.

        The restaurant receipt has three rates. Reading the legacy
        basic/reduced fields would flatten it to two and mislabel both; the
        items each carry their own rate, so they are the better source.
        """
        payload = {"receipt": dict(self.rest_payload["receipt"])}
        payload["receipt"].pop("vatSummary")
        mapped = map_receipt(payload, flatten=flatten_label)
        self.assertEqual(sorted(t["vat_rate"] for t in mapped["taxes"]),
                         [5.0, 19.0, 23.0])
        by_rate = {t["vat_rate"]: t for t in mapped["taxes"]}
        self.assertAlmostEqual(by_rate[5.0]["amount_untaxed"], 124.29, places=2)
        self.assertAlmostEqual(by_rate[5.0]["amount_tax"], 6.21, places=2)
        self.assertAlmostEqual(by_rate[23.0]["amount_untaxed"], 41.79, places=2)
        self.assertAlmostEqual(by_rate[23.0]["amount_tax"], 9.61, places=2)
        self.assertIn("derived from the items", mapped["warning"])

    def test_legacy_pair_is_used_only_with_neither_summary_nor_items(self):
        payload = {"receipt": dict(self.fuel_payload["receipt"])}
        payload["receipt"].pop("vatSummary")
        payload["receipt"]["items"] = []
        payload["receipt"].update({
            "vatRateBasic": 23.0, "taxBaseBasic": 47.03,
            "vatAmountBasic": 10.82,
        })
        mapped = map_receipt(payload, flatten=flatten_label)
        self.assertEqual(len(mapped["taxes"]), 1)
        self.assertEqual(mapped["taxes"][0]["vat_rate"], 23.0)
        self.assertIn("no items", mapped["warning"])

    def test_three_rate_recap_foots_to_the_total(self):
        base = sum(t["amount_untaxed"] for t in self.rest["taxes"])
        tax = sum(t["amount_tax"] for t in self.rest["taxes"])
        self.assertAlmostEqual(base, 166.08, places=2)
        self.assertAlmostEqual(tax, 15.82, places=2)
        self.assertAlmostEqual(base + tax, self.rest["amount_total"], places=2)

    # ------------------------------------------------------------------
    # the items
    # ------------------------------------------------------------------
    def test_item_price_is_the_line_total(self):
        """The twelve restaurant item prices sum to exactly the receipt total.

        Which is how we know ``price`` is the VAT-inclusive extended amount and
        not a unit price: the qty-2 lines divide cleanly (17.80/2 = 8.90).
        """
        self.assertEqual(len(self.rest["lines"]), 12)
        self.assertAlmostEqual(
            sum(line["amount_total"] for line in self.rest["lines"]),
            181.90, places=2)
        gimmari = next(l for l in self.rest["lines"] if "PREDJEDLO Č. 2" in l["name"])
        self.assertEqual(gimmari["quantity"], 2.0)
        self.assertEqual(gimmari["amount_total"], 17.80)

    def test_fuel_quantity_is_kept_but_not_turned_into_a_price(self):
        line = self.fuel["lines"][0]
        self.assertEqual(line["name"], "Benzín 95")
        self.assertEqual(line["quantity"], 31.17)
        self.assertEqual(line["amount_total"], 57.85)

    def test_multiline_item_name_is_flattened_never_split(self):
        """Modifiers come inside the name, with their money already in the line."""
        grill = next(l for l in self.rest["lines"] if l["name"].startswith("GRILOVANÉ"))
        self.assertNotIn("\n", grill["name"])
        self.assertIn("Príloha navyše", grill["name"])
        # 48.00 already includes the +3.00 modifier; it is one line, not three.
        self.assertEqual(grill["amount_total"], 48.00)
        self.assertEqual(len(self.rest["lines"]), 12)

    def test_zero_priced_item_is_kept(self):
        """Tap water at 19 % for 0.00 is why a bucket can have a zero base."""
        water = next(l for l in self.rest["lines"] if "Voda" in l["name"])
        self.assertEqual(water["amount_total"], 0.0)
        self.assertEqual(water["vat_rate"], 19.0)
        zero_bucket = next(t for t in self.rest["taxes"] if t["vat_rate"] == 19.0)
        self.assertEqual(zero_bucket["amount_untaxed"], 0.0)

    # ------------------------------------------------------------------
    # the seller
    # ------------------------------------------------------------------
    def test_vat_number_is_not_derived_from_the_tax_number(self):
        """Vzorová čerpacia stanica files in a VAT group, so the two are unrelated."""
        self.assertEqual(self.fuel["seller_vat"], "SK7199000006")
        self.assertEqual(self.fuel["seller_tax_id"], "2077000002")
        self.assertNotEqual(self.fuel["seller_vat"],
                            "SK" + self.fuel["seller_tax_id"])
        self.assertEqual(self.fuel["seller_reg_id"], "99000022")
        self.assertTrue(self.fuel["seller_vat_payer"])

    def test_seller_is_the_organization_and_premises_only_a_note(self):
        """The seat and the premises are different addresses.

        Vzorová čerpacia stanica's seat is in Bratislava-Vzorové Mesto; this receipt was issued at a
        motorway service station in Skúšobné Pole. Putting the premises on the partner
        would give the vendor the wrong address.
        """
        self.assertEqual(self.fuel["seller_name"], "Vzorová čerpacia stanica, a. s.")
        self.assertIn("Skúšobné Pole", self.fuel["premises_note"])
        self.assertNotIn("Vzorové Mesto", self.fuel["premises_note"] or "")

    # ------------------------------------------------------------------
    # identifiers and dates
    # ------------------------------------------------------------------
    def test_offline_receipt_yields_a_real_identifier(self):
        """An "OFF-LINE DOKLAD" is not permanently off-line.

        The QR carried no identifier, but the till synced afterwards, so the
        service hands one back — and that is the deduplication key, not the QR.
        """
        self.assertTrue(self.rest["receipt_uid"].startswith("O-"))
        self.assertEqual(len(self.rest["receipt_uid"]), 34)

    def test_issue_date_not_create_date(self):
        """They differ by a second on the fuel receipt."""
        receipt = self.fuel_payload["receipt"]
        self.assertEqual(receipt["issueDate"], "20.03.2026 09:36:36")
        self.assertEqual(receipt["createDate"], "20.03.2026 09:36:35")
        self.assertEqual(self.fuel["issue_date"].second, 36)

    def test_okp_is_upper_cased(self):
        """The service emits it in either case; the fuel one is lower."""
        self.assertEqual(self.fuel_payload["receipt"]["okp"],
                         "aaaa0011-bbbb0012-cccc0013-dddd0014-eeee0015")
        self.assertEqual(self.fuel["okp"],
                         "AAAA0011-BBBB0012-CCCC0013-DDDD0014-EEEE0015")
        self.assertEqual(self.rest["okp"], self.rest["okp"].upper())

    def test_empty_body_maps_to_nothing(self):
        self.assertEqual(map_receipt({"returnValue": 0, "receipt": None}), {})
        self.assertEqual(map_receipt(None), {})
