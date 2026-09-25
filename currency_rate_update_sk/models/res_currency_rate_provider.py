# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from datetime import timedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResCurrencyRateProvider(models.Model):
    """Adds a *previous-day fill* option, applicable to any provider.

    Central and commercial banks do not publish rates on weekends/holidays.
    When enabled, after every sync the last published rate is carried forward
    to each calendar day in the synced window so every day has an explicit
    ``res.currency.rate`` (SK: the reference rate of the preceding business day
    is what foreign-currency valuation falls back to anyway).
    """

    _inherit = "res.currency.rate.provider"

    fill_missing_days = fields.Boolean(
        string="Fill non-publishing days",
        default=True,
        help="After each update, carry the last published rate forward to "
        "weekends and holidays so every calendar day in the synced range has "
        "a rate. Idempotent — never overwrites a published rate.",
    )

    def _update(self, date_from, date_to, newest_only=False):
        res = super()._update(date_from, date_to, newest_only=newest_only)
        for provider in self.filtered("fill_missing_days"):
            provider._fill_missing_currency_rates(date_from, date_to)
        return res

    def _fill_missing_currency_rates(self, date_from, date_to):
        """Carry the last known rate forward across gap days in the window.

        For each of this provider's currencies, walk every day from
        ``date_from`` to ``date_to``; on a day that has no rate, create one
        equal to the most recent earlier rate (seeded from before the window).
        A day that already has a (published or filled) rate is left untouched
        and becomes the new carry-forward value.
        """
        self.ensure_one()
        Rate = self.env["res.currency.rate"]
        company = self.company_id
        one_day = timedelta(days=1)

        for currency in self.currency_ids:
            if currency == company.currency_id:
                continue

            seed = Rate.search(
                [
                    ("company_id", "=", company.id),
                    ("currency_id", "=", currency.id),
                    ("name", "<", date_from),
                ],
                order="name desc",
                limit=1,
            )
            last_rate = seed.rate if seed else None

            existing = Rate.search(
                [
                    ("company_id", "=", company.id),
                    ("currency_id", "=", currency.id),
                    ("name", ">=", date_from),
                    ("name", "<=", date_to),
                ]
            )
            by_date = {r.name: r.rate for r in existing}

            to_create = []
            day = date_from
            while day <= date_to:
                if day in by_date:
                    last_rate = by_date[day]
                elif last_rate is not None:
                    to_create.append(
                        {
                            "company_id": company.id,
                            "currency_id": currency.id,
                            "name": day,
                            "rate": last_rate,
                            "provider_id": self.id,
                        }
                    )
                day += one_day

            if to_create:
                Rate.create(to_create)
                _logger.debug(
                    "%s: filled %d gap day(s) for %s",
                    self.name,
                    len(to_create),
                    currency.name,
                )
