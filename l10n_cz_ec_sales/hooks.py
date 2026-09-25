# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Post-install: tag the standard CZ intra-EU supply taxes with their Souhrnné
hlášení (EC sales list) transaction code, so cssk.ec.summary collects them
without manual per-company tax configuration. Identifies the taxes by their
l10n_cz chart-template xmlids (account.<company>_<template>), so it is
translation- and rename-proof.
"""
import logging

_logger = logging.getLogger(__name__)

# l10n_cz tax template -> Souhrnné hlášení kód plnění (k_pln):
#   0 = dodání zboží do JČS, 1 = přemístění obch. majetku,
#   2 = třístranný obchod (prostřední osoba), 3 = poskytnutí služby
_EC_CODES = {
    "l10n_cz_supply_goods_eu": "0",
    "l10n_cz_supply_service_eu": "3",
}


def post_init_hook(env):
    for company in env["res.company"].search([("chart_template", "=", "cz")]):
        for template, code in _EC_CODES.items():
            tax = env.ref(
                "account.%s_%s" % (company.id, template), raise_if_not_found=False)
            if tax and not tax.cssk_ec_summary_code:
                tax.cssk_ec_summary_code = code
                _logger.info(
                    "l10n_cz_ec_sales: %s (%s) -> EC code %s",
                    tax.name, company.name, code)
