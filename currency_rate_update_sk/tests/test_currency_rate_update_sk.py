from datetime import date

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

# A faithful slice of https://www.vub.sk/Downloads/VUBteclist.txt
# (header lines 0-3, data from line 4; columns: Mena, Devíza nákup,
# Devíza stred, Devíza predaj, Valuta nákup, Valuta stred, Valuta predaj).
VUB_SAMPLE = """Kurzový listok VÚB, a.s.
platný od 11.06.2026 07:30

Mena     Devíza nákup      Devíza stred      Devíza predaj     Valuta nákup      Valuta stred      Valuta predaj
AUD      1,6780            1,6451            1,6122            1,7117            1,6451            1,5785
CAD      1,6417            1,6095            1,5773            1,6739            1,6095            1,5451
CZK      24,7110           24,1670           23,6230           24,9400           24,1670           23,3940
GBP      0,8793            0,8621            0,8449            0,8944            0,8621            0,8384
"""


@tagged("post_install", "-at_install")
class TestCurrencyRateUpdateSK(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.foreign = (
            cls.env["res.currency"]
            .with_context(active_test=False)
            .search([("name", "=", "GBP")], limit=1)
        )
        cls.foreign.active = True
        cls.Rate = cls.env["res.currency.rate"]

    def _provider(self, service="ECB"):
        return self.env["res.currency.rate.provider"].create(
            {
                "service": service,
                "company_id": self.company.id,
                "currency_ids": [(6, 0, self.foreign.ids)],
            }
        )

    def _clear_rates(self):
        self.Rate.search(
            [
                ("currency_id", "=", self.foreign.id),
                ("company_id", "=", self.company.id),
            ]
        ).unlink()

    def _rate_on(self, day):
        return self.Rate.search(
            [
                ("currency_id", "=", self.foreign.id),
                ("company_id", "=", self.company.id),
                ("name", "=", day),
            ],
            limit=1,
        )

    # ---- VÚB feed parsing (offline) --------------------------------------

    def test_vub_parse_takes_middle_rate(self):
        provider = self._provider("VUB")
        content = provider._vub_parse(VUB_SAMPLE, ["CZK", "GBP", "USD"])
        self.assertEqual(list(content.keys()), [date(2026, 6, 11)])
        rates = content[date(2026, 6, 11)]
        # Devíza stred column, not nákup/predaj.
        self.assertEqual(rates["CZK"], "24.167")
        self.assertEqual(rates["GBP"], "0.8621")
        # AUD/CAD present in feed but not requested -> excluded.
        self.assertNotIn("AUD", rates)
        self.assertNotIn("USD", rates)  # requested but absent from feed

    # ---- previous-day fill ----------------------------------------------

    def test_fill_seeds_from_before_window(self):
        provider = self._provider()
        self._clear_rates()
        self.Rate.create(
            {
                "company_id": self.company.id,
                "currency_id": self.foreign.id,
                "name": date(2026, 6, 5),  # Friday
                "rate": 0.85,
            }
        )
        # Window starts after the seed and has no published rate of its own.
        provider._fill_missing_currency_rates(date(2026, 6, 6), date(2026, 6, 8))
        for day in (date(2026, 6, 6), date(2026, 6, 7), date(2026, 6, 8)):
            self.assertAlmostEqual(self._rate_on(day).rate, 0.85, places=4)
        # Filled rows are attributed to the provider.
        self.assertEqual(self._rate_on(date(2026, 6, 7)).provider_id, provider)

    def test_fill_does_not_overwrite_published(self):
        provider = self._provider()
        self._clear_rates()
        self.Rate.create(
            {
                "company_id": self.company.id,
                "currency_id": self.foreign.id,
                "name": date(2026, 6, 5),
                "rate": 0.85,
            }
        )
        self.Rate.create(
            {
                "company_id": self.company.id,
                "currency_id": self.foreign.id,
                "name": date(2026, 6, 8),  # Monday, freshly published
                "rate": 0.90,
            }
        )
        provider._fill_missing_currency_rates(date(2026, 6, 5), date(2026, 6, 9))
        self.assertAlmostEqual(self._rate_on(date(2026, 6, 6)).rate, 0.85, places=4)
        self.assertAlmostEqual(self._rate_on(date(2026, 6, 7)).rate, 0.85, places=4)
        self.assertAlmostEqual(self._rate_on(date(2026, 6, 8)).rate, 0.90, places=4)
        # Tuesday carries the new Monday value forward, not the stale Friday one.
        self.assertAlmostEqual(self._rate_on(date(2026, 6, 9)).rate, 0.90, places=4)

    def test_fill_skips_leading_gap_without_seed(self):
        provider = self._provider()
        self._clear_rates()
        self.Rate.create(
            {
                "company_id": self.company.id,
                "currency_id": self.foreign.id,
                "name": date(2026, 6, 8),
                "rate": 0.90,
            }
        )
        provider._fill_missing_currency_rates(date(2026, 6, 5), date(2026, 6, 9))
        # No earlier rate to carry -> leading days stay empty.
        self.assertFalse(self._rate_on(date(2026, 6, 5)))
        self.assertFalse(self._rate_on(date(2026, 6, 7)))
        self.assertAlmostEqual(self._rate_on(date(2026, 6, 9)).rate, 0.90, places=4)
