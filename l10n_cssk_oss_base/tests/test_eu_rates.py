# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.addons.l10n_eu_oss.models import res_company as oss_res_company
from odoo.addons.l10n_eu_oss.models.eu_tax_map import EU_TAX_MAP
from odoo.tests import TransactionCase, tagged

from ..models import res_company as our_res_company
from ..models.cssk_oss_return import CsskOssReturn
from ..models.eu_rates import (
    oss_country_code, rate_type, sk_five_percent_overlay, standard_rate)


@tagged("post_install", "-at_install")
class TestSkFivePercentOverlay(TransactionCase):
    """What the Slovak 5 % overlay adds, and that it adds it nowhere else."""

    def test_sk_five_follows_core_sk_ten(self):
        overlay = sk_five_percent_overlay(EU_TAX_MAP)
        for dest in ("DE", "CZ", "AT", "FR", "IT"):
            self.assertEqual(overlay[("SK", 5.0, dest)],
                             EU_TAX_MAP[("SK", 10.0, dest)], dest)
        self.assertNotIn(("SK", 5.0, "SK"), overlay)

    def test_lowest_reduced_rate_goes_to_sk_five(self):
        overlay = sk_five_percent_overlay(EU_TAX_MAP)
        self.assertEqual(overlay[("DE", 7.0, "SK")], 5.0)
        self.assertEqual(overlay[("FR", 2.1, "SK")], 5.0)
        # a higher reduced tier and every standard rate stay as core has them
        self.assertNotIn(("FR", 5.5, "SK"), overlay)
        self.assertNotIn(("DE", 19.0, "SK"), overlay)

    def test_czech_twelve_percent_goes_to_sk_five(self):
        """CZ merged 10 % and 15 % into 12 % in 2024; core still lists 10."""
        overlay = sk_five_percent_overlay(EU_TAX_MAP)
        self.assertEqual(overlay[("CZ", 12.0, "SK")], 5.0)
        self.assertEqual(overlay[("CZ", 10.0, "SK")], 5.0)
        self.assertNotIn(("CZ", 15.0, "SK"), overlay)
        self.assertNotIn(("CZ", 21.0, "SK"), overlay)

    def test_core_dict_is_never_mutated(self):
        """A database without this module must keep seeing core's map."""
        before = dict(EU_TAX_MAP)
        sk_five_percent_overlay(EU_TAX_MAP)
        self.assertEqual(EU_TAX_MAP, before)
        self.assertEqual(EU_TAX_MAP[("CZ", 12.0, "SK")], 19.0)

    def test_the_scoped_lookup_is_inert_outside_a_mapping_run(self):
        scoped = oss_res_company.EU_TAX_MAP
        self.assertIsInstance(scoped, our_res_company.ScopedEuTaxMap)
        self.assertEqual(scoped.get(("CZ", 12.0, "SK")), 19.0)
        self.assertIsNone(scoped.get(("SK", 5.0, "DE")))
        token = our_res_company._OVERLAY.set(
            sk_five_percent_overlay(scoped.base))
        try:
            self.assertEqual(scoped.get(("CZ", 12.0, "SK")), 5.0)
            self.assertEqual(scoped.get(("SK", 5.0, "DE")), 7.0)
        finally:
            our_res_company._OVERLAY.reset(token)
        self.assertEqual(scoped.get(("CZ", 12.0, "SK")), 19.0)


@tagged("post_install", "-at_install")
class TestOssRateFacts(TransactionCase):

    def test_standard_rate_follows_the_date(self):
        self.assertEqual(standard_rate("SK", date(2024, 12, 31)), 20.0)
        self.assertEqual(standard_rate("SK", date(2025, 1, 1)), 23.0)
        self.assertEqual(standard_rate("EE", date(2025, 6, 30)), 22.0)
        self.assertEqual(standard_rate("EE", date(2025, 9, 30)), 24.0)
        self.assertEqual(standard_rate("LU", date(2023, 6, 30)), 16.0)

    def test_rate_type(self):
        self.assertEqual(rate_type("DE", 19.0, date(2025, 9, 30)), "standard")
        self.assertEqual(rate_type("DE", 7.0, date(2025, 9, 30)), "reduced")
        self.assertEqual(rate_type("SK", 20.0, date(2025, 9, 30)), "reduced")
        self.assertIsNone(rate_type("XX", 20.0, date(2025, 9, 30)))

    def test_greece_is_el_on_the_forms(self):
        self.assertEqual(oss_country_code("GR"), "EL")
        self.assertEqual(oss_country_code("DE"), "DE")

    def test_due_date_is_end_of_the_following_month(self):
        self.assertEqual(CsskOssReturn._cssk_oss_due_date(2022, 3),
                         date(2022, 10, 31))
        self.assertEqual(CsskOssReturn._cssk_oss_due_date(2022, 4),
                         date(2023, 1, 31))
        self.assertEqual(CsskOssReturn._cssk_oss_due_date(2024, 1),
                         date(2024, 4, 30))
