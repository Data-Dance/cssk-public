# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import date
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

GET = "odoo.addons.currency_rate_update_cz.models.res_currency_rate_provider_CNB.requests.get"

CNB_SAMPLE = """12 Jun 2026 #112
Country|Currency|Amount|Code|Rate
EMU|euro|1|EUR|24.170
Japan|yen|100|JPY|13.043
USA|dollar|1|USD|20.894
"""


@tagged("post_install", "-at_install")
class TestCzFx(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["res.currency.rate.provider"].new({"service": "CNB"})

    def test_parse_foreign_per_czk(self):
        content = self.provider._cnb_parse(CNB_SAMPLE, ["EUR", "JPY", "USD"])
        self.assertEqual(list(content.keys()), [date(2026, 6, 12)])
        rates = content[date(2026, 6, 12)]
        # 1 EUR = 24.170 CZK -> EUR per CZK = 1/24.170
        self.assertAlmostEqual(float(rates["EUR"]), 1 / 24.170, places=6)
        # 100 JPY = 13.043 CZK -> JPY per CZK = 100/13.043
        self.assertAlmostEqual(float(rates["JPY"]), 100 / 13.043, places=6)
        self.assertAlmostEqual(float(rates["USD"]), 1 / 20.894, places=6)

    def test_obtain_rates_uses_feed(self):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.text = CNB_SAMPLE
        with patch(GET, return_value=fake) as mock_get:
            content = self.provider._obtain_rates(
                "CZK", ["EUR"], date(2026, 6, 1), date(2026, 6, 12))
        # the date param is passed in DD.MM.YYYY
        self.assertEqual(mock_get.call_args.kwargs["params"]["date"], "12.06.2026")
        self.assertIn("EUR", content[date(2026, 6, 12)])
